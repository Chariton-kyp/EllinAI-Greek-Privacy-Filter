"""Train v3 teacher via Unsloth LoRA Q4 SFT.

Default base: google/gemma-4-31B-it (Apache 2.0, multilingual incl. Greek).
Alternative: Qwen/Qwen3.6-35B-A3B-Instruct (Apache 2.0, MoE).

Inputs:
    data/processed/v3_chat/{train,validation}.jsonl
    configs/v3_distillation.yaml

Outputs:
    artifacts/v3/teacher/<run-id>/lora_adapters/
    artifacts/v3/teacher/<run-id>/training_metrics.json

Designed for AWS g6e.xlarge spot (L40S 48GB) but also runs on RTX 4080
12GB via Unsloth offload (slower, training-only — not recommended for
the 31B teacher).

Usage:
    python scripts/v3/train_teacher_qwen36.py \\
        --config configs/v3_distillation.yaml \\
        --output-dir artifacts/v3/teacher/run-$(date -u +%Y%m%dT%H%M%SZ) \\
        --train-jsonl data/processed/v3_chat/train.jsonl \\
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


def to_chat_text(rec: dict, tokenizer) -> str:
    """Apply the model's chat template to a {messages: [...]} record."""
    return tokenizer.apply_chat_template(
        rec["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--config", type=Path,
                    default=Path("configs/v3_distillation.yaml"))
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--train-jsonl", type=Path,
                    default=Path("data/processed/v3_chat/train.jsonl"))
    p.add_argument("--eval-jsonl", type=Path,
                    default=Path("data/processed/v3_chat/validation.jsonl"))
    p.add_argument("--model-override", default=None,
                    help="Override teacher.hf_id from config.")
    p.add_argument("--max-train-samples", type=int, default=None,
                    help="Subset for fast pilot runs (default: all).")
    p.add_argument("--max-eval-samples", type=int, default=None,
                    help="Subset eval set for faster eval rounds. "
                         "Full set on 14k+ records takes ~50 min/round on L40S; "
                         "1000 random samples gives a stable eval_loss in ~3 min.")
    args = p.parse_args()

    cfg = load_yaml(args.config)
    teacher = cfg["teacher"]
    hf_id = args.model_override or teacher["hf_id"]
    sft_cfg = teacher["sft"]
    lora_cfg = teacher["lora"]

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Lazy imports — keep arg-parse fast
    print(f"[v3-teacher] loading {hf_id} ({4 if teacher['load_in_4bit'] else 16}-bit)...",
          flush=True)
    from unsloth import FastLanguageModel  # type: ignore
    from datasets import load_dataset      # type: ignore
    from trl import SFTTrainer, SFTConfig  # type: ignore

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=hf_id,
        max_seq_length=sft_cfg["max_seq_length"],
        dtype=None,
        load_in_4bit=teacher["load_in_4bit"],
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["alpha"],
        lora_dropout=lora_cfg["dropout"],
        target_modules=lora_cfg["target_modules"],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=sft_cfg["seed"],
        use_rslora=False,
        loftq_config=None,
    )

    train_ds = load_dataset("json", data_files=str(args.train_jsonl),
                              split="train")
    eval_ds = load_dataset("json", data_files=str(args.eval_jsonl),
                             split="train")

    if args.max_train_samples:
        train_ds = train_ds.select(range(min(len(train_ds), args.max_train_samples)))
        print(f"[v3-teacher] limited to {len(train_ds)} train samples", flush=True)
    if args.max_eval_samples:
        eval_ds = eval_ds.shuffle(seed=sft_cfg["seed"]).select(
            range(min(len(eval_ds), args.max_eval_samples))
        )
        print(f"[v3-teacher] limited to {len(eval_ds)} eval samples (seed={sft_cfg['seed']})",
              flush=True)

    # Pre-tokenize the dataset ourselves. In TRL ≥ 0.21 with transformers
    # 5.x the SFTTrainer's auto-tokenization path via `dataset_text_field`
    # has shifted under us twice (pilots v8/v9): the trainer's data
    # collator then calls `tokenizer.pad(batch)` and crashes with
    #   "ValueError: ... that includes input_ids, but you provided ['text']"
    # because the column was never tokenized. Pre-tokenizing makes us
    # version-agnostic — the dataset already carries `input_ids` /
    # `attention_mask` / `labels`, so the default collator just pads.
    max_seq = sft_cfg["max_seq_length"]

    def _to_blocks(content):
        # Gemma 4 (multimodal) chat template expects content to be a list of
        # typed blocks (e.g. [{"type":"text","text":...}]). Plain string
        # content trips a TypeError inside transformers' template renderer:
        #   TypeError: 'NoneType' object is not subscriptable (text[0])
        # Wrap any string content in a single text block; pass through if
        # already a list (vision/audio prep happens elsewhere).
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
        # Pass text= as a kwarg, not positional. Gemma4Processor
        # (the wrapper "tokenizer" returned for Gemma 4) routes the first
        # positional arg through a multimodal-aware patched call that
        # surfaces it as text=None when there are no images/videos. The
        # processor then tries text[0] and crashes with
        #   TypeError: 'NoneType' object is not subscriptable
        # Passing text= explicitly (kwarg) avoids that branch.
        enc = tokenizer(
            text=texts,
            truncation=True,
            max_length=max_seq,
            padding=False,
            return_attention_mask=True,
        )

        # Gemma4Processor wraps each example's input_ids in an extra outer
        # list (multimodal "channel" axis). Flatten that wrap so the
        # default data collator gets list[int] per example, not
        # list[list[int]]. Otherwise pad() raises:
        #   "your features (`labels` in this case) have excessive nesting"
        def _flatten_one(x):
            while isinstance(x, list) and len(x) > 0 and isinstance(x[0], list):
                x = x[0]
            return list(x)

        # Return ONLY the three columns the default collator pads on
        # text-only causal LM. Gemma4Processor adds `mm_token_type_ids`
        # (multimodal channel mask) which the collator can't pad as ints
        # and trips ValueError "excessive nesting (`labels` in this case)"
        # at eval time. Reconstruct as a plain dict to also avoid the
        # BatchEncoding wrapper datasets/Arrow handles oddly.
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
        num_train_epochs=sft_cfg["epochs"],
        per_device_train_batch_size=sft_cfg["per_device_batch_size"],
        gradient_accumulation_steps=sft_cfg["gradient_accumulation_steps"],
        learning_rate=sft_cfg["learning_rate"],
        warmup_steps=sft_cfg.get("warmup_steps", 0),
        warmup_ratio=sft_cfg.get("warmup_ratio", 0.0),
        weight_decay=sft_cfg["weight_decay"],
        optim=sft_cfg["optim"],
        save_strategy="steps",
        save_steps=sft_cfg["save_steps"],
        eval_strategy="steps",
        eval_steps=sft_cfg["eval_steps"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=20,
        report_to="none",
        bf16=True,
        gradient_checkpointing=True,
        save_total_limit=2,
        seed=sft_cfg["seed"],
        # max_length kept for collator-side truncation safety; dataset is
        # already tokenized so the trainer doesn't have to re-process text.
        max_length=max_seq,
        packing=False,
    )

    # Gemma 4's `tokenizer` is a multimodal Gemma4Processor. The Trainer's
    # default collator + .pad() expect a plain text tokenizer, so route
    # through `processor.tokenizer` if present (Gemma 4) and fall back to
    # the object itself for text-only models (gemma-3, qwen, etc).
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

    # Save LoRA adapters (NOT merged base — saves 60GB+ disk)
    final = args.output_dir / "lora_adapters"
    trainer.save_model(str(final))
    tokenizer.save_pretrained(str(final))

    metrics = {
        "hf_id": hf_id,
        "elapsed_seconds": elapsed,
        "train_samples": len(train_ds),
        "eval_samples": len(eval_ds),
        "training_loss": train_result.training_loss,
        "config": {
            "lora": lora_cfg,
            "sft": sft_cfg,
        },
    }
    with (args.output_dir / "training_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"[v3-teacher] DONE  elapsed={elapsed/60:.1f}min  loss={train_result.training_loss:.4f}",
          flush=True)
    print(f"[v3-teacher] adapter saved to: {final}", flush=True)


if __name__ == "__main__":
    main()
