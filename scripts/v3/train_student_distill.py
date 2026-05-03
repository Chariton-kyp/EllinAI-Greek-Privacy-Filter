"""Train v3 student via Unsloth SFT (LoRA Q4) on gold + pseudo-labels.

One trainer, parametrised for any of the 5 student tiers in
`configs/v3_distillation.yaml`:

    --tier lite    privacy-filter 1.4B (token-classifier — separate path)
    --tier mini    gemma-4-E2B
    --tier pro     gemma-4-E4B
    --tier max     Qwen3-4B (or gemma-4-26B-A4B)
    --tier ultra   gemma-4-31B (= teacher, no extra train)

Inputs (combined automatically):
    data/processed/v3_chat/train.jsonl                  ← v2.13 gold
    data/processed/v3_pseudo/pseudo_labels.jsonl        ← teacher pseudo (after convert)
    data/processed/v3_chat/validation.jsonl             ← held-out

The lite tier (privacy-filter 1.4B) uses the EXISTING token-classifier
training path — re-use scripts/run_opf_train.py with the v2.13+pseudo
combined dataset; this script is for causal-LM students only.

Usage:
    python scripts/v3/train_student_distill.py \\
        --config configs/v3_distillation.yaml \\
        --tier mini \\
        --output-dir artifacts/v3/students/mini-$(date -u +%Y%m%dT%H%M%SZ) \\
        --train-jsonl data/processed/v3_chat/train_with_pseudo.jsonl \\
        --eval-jsonl  data/processed/v3_chat/validation.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def load_yaml(path: Path) -> dict:
    import yaml  # type: ignore
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--config", type=Path,
                    default=Path("configs/v3_distillation.yaml"))
    p.add_argument("--tier", required=True,
                    choices=["mini", "pro", "max"],
                    help="lite uses run_opf_train.py instead; ultra is teacher.")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--train-jsonl", type=Path, required=True)
    p.add_argument("--eval-jsonl", type=Path, required=True)
    p.add_argument("--max-train-samples", type=int, default=None)
    args = p.parse_args()

    cfg = load_yaml(args.config)
    student_cfg = next((s for s in cfg["students"] if s["name"] == args.tier), None)
    if student_cfg is None:
        raise SystemExit(f"FAIL: tier '{args.tier}' not in config")
    if student_cfg.get("architecture") != "causal_lm":
        raise SystemExit(f"FAIL: tier '{args.tier}' is not causal_lm; use a different trainer.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    hf_id = student_cfg["hf_id"]
    sft_cfg = student_cfg["sft"]
    lora_cfg = student_cfg.get("lora", {"r": 16, "alpha": 32, "dropout": 0.05,
                                         "target_modules": [
                                             "q_proj", "k_proj", "v_proj", "o_proj",
                                             "gate_proj", "up_proj", "down_proj",
                                         ]})

    print(f"[v3-student/{args.tier}] loading {hf_id} (4-bit + LoRA)...", flush=True)
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import SFTTrainer, SFTConfig

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=hf_id,
        max_seq_length=sft_cfg.get("max_seq_length", 4096),
        dtype=None,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["alpha"],
        lora_dropout=lora_cfg.get("dropout", 0.05),
        target_modules=lora_cfg.get("target_modules", [
            "q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj",
        ]),
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=2042,
    )

    train_ds = load_dataset("json", data_files=str(args.train_jsonl), split="train")
    eval_ds = load_dataset("json", data_files=str(args.eval_jsonl), split="train")

    if args.max_train_samples:
        train_ds = train_ds.select(range(min(len(train_ds), args.max_train_samples)))

    # Pre-tokenize ourselves — same rationale as train_teacher.py: TRL ≥ 0.21
    # with transformers 5.x dropped reliable `dataset_text_field` auto-tokenize.
    max_seq = sft_cfg.get("max_seq_length", 4096)

    def _to_blocks(content):
        # Gemma 4 chat template needs content as multimodal blocks
        # (string content → TypeError on text[0] in template renderer).
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        return content

    def _format_and_tokenize(batch):
        texts = []
        for convo in batch["messages"]:
            normalized = [
                {"role": m["role"], "content": _to_blocks(m["content"])}
                for m in convo
            ]
            texts.append(
                tokenizer.apply_chat_template(
                    normalized, tokenize=False, add_generation_prompt=False,
                )
            )
        enc = tokenizer(
            text=texts,
            truncation=True,
            max_length=max_seq,
            padding=False,
            return_attention_mask=True,
        )

        # Drop Gemma4Processor's `mm_token_type_ids` and any other extra
        # columns: the default collator can't pad those as ints, which
        # crashes at eval. See train_teacher.py for full reasoning.
        def _flatten_one(x):
            while isinstance(x, list) and len(x) > 0 and isinstance(x[0], list):
                x = x[0]
            return list(x)

        return {
            "input_ids": [_flatten_one(ids) for ids in enc["input_ids"]],
            "attention_mask": [_flatten_one(a) for a in enc["attention_mask"]],
            "labels": [_flatten_one(ids) for ids in enc["input_ids"]],
        }

    train_ds = train_ds.map(_format_and_tokenize, batched=True,
                              remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(_format_and_tokenize, batched=True,
                            remove_columns=eval_ds.column_names)

    sft_config = SFTConfig(
        output_dir=str(args.output_dir / "checkpoints"),
        num_train_epochs=sft_cfg.get("epochs", 2),
        per_device_train_batch_size=sft_cfg.get("batch_size", 4),
        gradient_accumulation_steps=sft_cfg.get("grad_accum", 4),
        learning_rate=sft_cfg.get("lr", 2e-4),
        warmup_ratio=0.03,
        weight_decay=0.01,
        optim="adamw_8bit",
        save_strategy="steps",
        save_steps=500,
        eval_strategy="steps",
        eval_steps=500,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=20,
        report_to="none",
        bf16=True,
        gradient_checkpointing=True,
        save_total_limit=2,
        seed=2042,
        max_length=max_seq,
        packing=False,
    )

    text_tokenizer = getattr(tokenizer, "tokenizer", tokenizer)
    from transformers import DataCollatorForSeq2Seq  # type: ignore
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=text_tokenizer,
        padding=True,
        return_tensors="pt",
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=text_tokenizer,  # `tokenizer=` removed in TRL ≥ 0.21
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=sft_config,
        data_collator=data_collator,
    )

    t0 = time.time()
    train_result = trainer.train()
    elapsed = time.time() - t0

    final = args.output_dir / "lora_adapters"
    trainer.save_model(str(final))
    tokenizer.save_pretrained(str(final))

    metrics = {
        "tier": args.tier,
        "hf_id": hf_id,
        "elapsed_seconds": elapsed,
        "train_samples": len(train_ds),
        "eval_samples": len(eval_ds),
        "training_loss": train_result.training_loss,
        "expected_f1": student_cfg.get("expected_f1"),
    }
    with (args.output_dir / "training_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"[v3-student/{args.tier}] DONE elapsed={elapsed/60:.1f}min "
          f"loss={train_result.training_loss:.4f}", flush=True)


if __name__ == "__main__":
    main()
