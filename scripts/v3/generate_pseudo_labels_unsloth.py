"""Generate pseudo-labels via Unsloth direct inference (no vLLM, no merge).

Loads base + LoRA via Unsloth FastLanguageModel in 4-bit (~22GB VRAM for 31B),
runs batched inference over Greek corpus, parses JSON-spans output, resolves
to char offsets via strict cursor, and writes OPF-format JSONL.

Why this approach (vs vLLM):
  - Unsloth bnb-4bit + LoRA inference fits comfortably in 48GB L40S
  - No merge step (avoids dequantize+save 60GB+ bf16 disk pressure)
  - No serving layer (eliminates entire class of HTTP/protocol bugs)
  - Reuses the EXACT model object that was trained, so no train-inference
    template drift

Usage:
    python scripts/v3/generate_pseudo_labels_unsloth.py \\
        --base-model unsloth/gemma-4-31B-it-unsloth-bnb-4bit \\
        --lora-adapter /opt/gpf/teacher_adapter/<run-id>/lora_adapters \\
        --input data/processed/v3_corpus/greek_corpus.jsonl \\
        --output data/processed/v3_pseudo/pseudo_labels.jsonl \\
        --batch-size 8 --max-records 500000
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_JSON_LIST_RE = re.compile(r"\[\s*(?:\{.*?\})?\s*(?:,\s*\{.*?\}\s*)*\]", re.DOTALL)


SYSTEM_PROMPT = (
    "Είσαι σύστημα ανίχνευσης ευαίσθητων προσωπικών δεδομένων (PII) σε "
    "ελληνικό κείμενο. Όταν σου δίνεται ένα κείμενο, απαντάς ΑΠΟΚΛΕΙΣΤΙΚΑ "
    "με μια έγκυρη JSON λίστα της μορφής:\n"
    "  [{\"label\": \"<class>\", \"value\": \"<αυτούσιο απόσπασμα>\"}, ...]\n"
    "Εντόπισε τα PII στη σειρά που εμφανίζονται στο κείμενο (αριστερά → δεξιά). "
    "Αν δεν υπάρχει κανένα PII, απάντησε []. ΟΧΙ σχόλια, ΟΧΙ markdown."
)


def parse_spans(content: str):
    content = content.strip()
    try:
        v = json.loads(content)
        if isinstance(v, list):
            return [s for s in v if isinstance(s, dict)]
    except json.JSONDecodeError:
        pass
    m = _JSON_LIST_RE.search(content)
    if not m:
        return None
    try:
        v = json.loads(m.group(0))
        return [s for s in v if isinstance(s, dict)] if isinstance(v, list) else None
    except json.JSONDecodeError:
        return None


def resolve_offsets(text: str, spans):
    """Strict cursor resolver. Returns None on any unresolvable span."""
    if spans is None:
        return None
    out = []
    cursor = 0
    for s in spans:
        lbl = s.get("label")
        val = s.get("value")
        if not lbl or not val:
            return None
        idx = text.find(val, cursor)
        if idx < 0:
            return None
        out.append({"category": lbl, "start": idx, "end": idx + len(val)})
        cursor = idx + len(val)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--base-model", required=True,
                    help="Base model HF id (e.g. unsloth/gemma-4-31B-it-unsloth-bnb-4bit)")
    p.add_argument("--lora-adapter", required=True,
                    help="Path to lora_adapters/ directory from train_teacher.py output")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-records", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--max-seq-length", type=int, default=2048)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--resume", action="store_true",
                    help="Skip records already present in output (by text hash).")
    args = p.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    seen: set[int] = set()
    if args.resume and args.output.exists():
        with args.output.open(encoding="utf-8") as f:
            for line in f:
                try:
                    seen.add(hash(json.loads(line)["text"]))
                except (json.JSONDecodeError, KeyError):
                    continue
        print(f"[resume] skipping {len(seen)} already-labelled", flush=True)

    print(f"[unsloth] loading {args.base_model} + LoRA {args.lora_adapter}", flush=True)
    from unsloth import FastLanguageModel  # type: ignore
    import torch

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    # Load LoRA adapter into the base
    from peft import PeftModel  # type: ignore
    model = PeftModel.from_pretrained(model, args.lora_adapter)
    FastLanguageModel.for_inference(model)
    model.eval()

    # Load corpus
    records = []
    with args.input.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = rec.get("text", "")
            if not text or hash(text) in seen:
                continue
            records.append(rec)
            if args.max_records and len(records) >= args.max_records:
                break
    print(f"[unsloth] {len(records)} records to label", flush=True)

    # Batched inference
    written = 0
    skipped_parse = 0
    skipped_offsets = 0
    t_start = time.time()

    with args.output.open("a" if args.resume else "w", encoding="utf-8") as fout:
        for i in range(0, len(records), args.batch_size):
            batch = records[i:i + args.batch_size]
            prompts = []
            for rec in batch:
                msg = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": rec["text"]},
                ]
                prompts.append(tokenizer.apply_chat_template(
                    msg, tokenize=False, add_generation_prompt=True))

            inputs = tokenizer(prompts, return_tensors="pt", padding=True,
                                truncation=True, max_length=args.max_seq_length).to("cuda")

            with torch.inference_mode():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False if args.temperature == 0.0 else True,
                    temperature=max(args.temperature, 0.01),
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                )

            # Decode only the generated portion
            for rec, output_ids, input_ids in zip(batch, outputs, inputs["input_ids"]):
                gen_ids = output_ids[len(input_ids):]
                content = tokenizer.decode(gen_ids, skip_special_tokens=True)
                spans = parse_spans(content)
                if spans is None:
                    skipped_parse += 1
                    continue
                resolved = resolve_offsets(rec["text"], spans)
                if resolved is None:
                    skipped_offsets += 1
                    continue
                out_rec = {
                    "text": rec["text"],
                    "label": resolved,
                    "info": {
                        "source": "v3_pseudo",
                        "teacher": args.base_model,
                        "src_corpus": rec.get("info", {}).get("source", "unknown"),
                        "src_license": rec.get("info", {}).get("license", "unknown"),
                    },
                }
                fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
                written += 1

            fout.flush()

            if (i // args.batch_size) % 10 == 0:
                elapsed = time.time() - t_start
                rate = written / max(elapsed, 1)
                pct = (i + len(batch)) / max(len(records), 1) * 100
                print(f"[{written:>6}/{len(records)}  {pct:5.1f}%]  "
                      f"rate={rate*60:.1f}/min  "
                      f"parse_drop={skipped_parse}  offset_drop={skipped_offsets}",
                      flush=True)

    elapsed = time.time() - t_start
    print(f"\nDONE  written={written} parse_drop={skipped_parse} "
          f"offset_drop={skipped_offsets} elapsed={elapsed/60:.1f}min")


if __name__ == "__main__":
    main()
