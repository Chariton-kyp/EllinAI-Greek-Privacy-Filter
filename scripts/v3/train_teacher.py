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
    from trl import SFTTrainer             # type: ignore
    from transformers import TrainingArguments  # type: ignore

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

    def _format(rec):
        return {"text": to_chat_text(rec, tokenizer)}

    train_ds = train_ds.map(_format, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(_format, remove_columns=eval_ds.column_names)

    training_args = TrainingArguments(
        output_dir=str(args.output_dir / "checkpoints"),
        num_train_epochs=sft_cfg["epochs"],
        per_device_train_batch_size=sft_cfg["per_device_batch_size"],
        gradient_accumulation_steps=sft_cfg["gradient_accumulation_steps"],
        learning_rate=sft_cfg["learning_rate"],
        warmup_ratio=sft_cfg["warmup_ratio"],
        weight_decay=sft_cfg["weight_decay"],
        optim=sft_cfg["optim"],
        save_steps=sft_cfg["save_steps"],
        eval_steps=sft_cfg["eval_steps"],
        logging_steps=20,
        report_to="none",
        bf16=True,
        gradient_checkpointing=True,
        save_total_limit=2,
        seed=sft_cfg["seed"],
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        dataset_text_field="text",
        max_seq_length=sft_cfg["max_seq_length"],
        args=training_args,
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
