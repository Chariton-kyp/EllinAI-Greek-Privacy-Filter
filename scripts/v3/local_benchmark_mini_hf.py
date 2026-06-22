"""Run the Greek PII Public Benchmark v1 against Mini v3 (Gemma 4 2B Q4 LoRA).

HF-native loading path: loads the base model + LoRA adapter with plain
transformers + peft, WITHOUT importing unsloth. This deliberately avoids
the unsloth_zoo gemma4 temporary-patch bug ("num_kv_shared_layers is 0")
that breaks FastLanguageModel.from_pretrained on this checkpoint. The
gemma4 architecture loads natively in a recent transformers build.

Output: artifacts/metrics/benchmark_mini.json (same schema as the OPF
3-way script, mergeable into the same reports).

Usage (inside a container with a recent transformers + peft + bnb):
    docker run --rm --gpus all --ipc=host --shm-size=8g \\
      -v $PWD:/workspace/gpf -v /tmp/hf-cache:/workspace/.cache/huggingface \\
      -e HF_HOME=/workspace/.cache/huggingface \\
      --entrypoint /bin/bash unsloth/unsloth:latest -c '
        pip install -q --upgrade transformers peft bitsandbytes accelerate
        python /workspace/gpf/scripts/v3/local_benchmark_mini_hf.py'
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "greek_pii_public_v1" / "cases.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_mini.json"
DEFAULT_LORA = PROJECT_ROOT / "artifacts" / "v3" / "students" / "mini-local"

SYSTEM_PROMPT = (
    "Είσαι Greek PII detector. Επιστρέφεις ΑΥΣΤΗΡΑ JSON λίστα με το format "
    '[{"label": "<class>", "value": "<exact substring>"}, ...]. '
    "Κλάσεις: account_number, adt, afm, ama, amka, card_pan, cvv, "
    "driver_license, gemi, iban_gr, imei, ip_address, license_plate, "
    "mac_address, passport, pcn, private_address, private_date, "
    "private_email, private_person, private_phone, private_url, secret, "
    "vehicle_vin. Αν το κείμενο δεν περιέχει PII, επιστρέφεις []."
)

_JSON_LIST_RE = re.compile(r"\[\s*(?:\{.*?\})?\s*(?:,\s*\{.*?\}\s*)*\]", re.DOTALL)


def parse_spans(content: str) -> list[dict]:
    content = content.strip()
    try:
        v = json.loads(content)
        if isinstance(v, list):
            return [s for s in v if isinstance(s, dict)]
    except json.JSONDecodeError:
        pass
    m = _JSON_LIST_RE.search(content)
    if not m:
        return []
    try:
        v = json.loads(m.group(0))
        return [s for s in v if isinstance(s, dict)] if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def resolve_offsets(text: str, spans: list[dict]) -> list[dict]:
    out: list[dict] = []
    cursor = 0
    for s in spans:
        lbl = s.get("label")
        val = s.get("value")
        if not lbl or not val:
            continue
        idx = text.find(val, cursor)
        if idx < 0:
            idx = text.find(val)
            if idx < 0:
                continue
        out.append({"label": lbl, "start": idx, "end": idx + len(val), "text": val})
        cursor = idx + len(val)
    return out


def overlap(a: dict, b: dict) -> int:
    return max(0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--lora-adapter", type=Path, default=DEFAULT_LORA)
    p.add_argument("--base-model", default=None,
                    help="Override base model id (default: read from adapter_config.json)")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--max-seq-length", type=int, default=4096)
    args = p.parse_args()

    cases: list[dict] = []
    with args.benchmark.open(encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))
    print(f"loaded {len(cases)} cases", flush=True)

    # Resolve base model id from adapter config unless overridden.
    base_id = args.base_model
    if not base_id:
        with (args.lora_adapter / "adapter_config.json").open(encoding="utf-8") as f:
            base_id = json.load(f)["base_model_name_or_path"]
    print(f"[hf] base={base_id}  adapter={args.lora_adapter}", flush=True)

    # IMPORTANT: do NOT import unsloth. Plain transformers + peft path.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print("[hf] transformers loading base (4-bit, native gemma4)...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_id,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    # Gemma 4 wraps its projection layers in Gemma4ClippableLinear, which
    # PEFT's LoRA injector does not recognise (only plain nn.Linear /
    # Linear4bit etc). Unwrap each wrapper to its inner Linear4bit so PEFT
    # can attach the adapter. The clipping wrapper only adds an output
    # clamp; the underlying quantized Linear carries the trained weights
    # the adapter targets.
    import torch.nn as nn  # noqa: F401
    unwrapped = 0
    for _mod in model.modules():
        for _child_name, _child in list(_mod.named_children()):
            if type(_child).__name__ == "Gemma4ClippableLinear" and hasattr(_child, "linear"):
                setattr(_mod, _child_name, _child.linear)
                unwrapped += 1
    print(f"[hf] unwrapped {unwrapped} Gemma4ClippableLinear -> Linear4bit", flush=True)

    print("[hf] attaching LoRA adapter via peft...", flush=True)
    model = PeftModel.from_pretrained(model, str(args.lora_adapter))
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(str(args.lora_adapter), trust_remote_code=True)
    # Some Gemma4 tokenizers wrap a text tokenizer; unwrap if needed.
    text_tokenizer = getattr(tokenizer, "tokenizer", tokenizer)

    def build_prompt(user_text: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        try:
            return tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            # Fallback: simple concatenation if chat template rejects plain strings.
            return f"{SYSTEM_PROMPT}\n\n{user_text}\n\nJSON:"

    by_class_tp: dict = {}
    by_class_fn: dict = {}
    by_class_fp: dict = {}
    triages: list[dict] = []
    per_case: list[dict] = []

    t_start = time.time()
    for i, case in enumerate(cases):
        prompt = build_prompt(case["text"])
        enc = text_tokenizer(prompt, return_tensors="pt", truncation=True,
                              max_length=args.max_seq_length)
        enc = {k: v.to(model.device) for k, v in enc.items()}

        with torch.inference_mode():
            output = model.generate(
                **enc,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=text_tokenizer.pad_token_id or text_tokenizer.eos_token_id,
            )

        gen_ids = output[0][enc["input_ids"].shape[1]:]
        content = text_tokenizer.decode(gen_ids, skip_special_tokens=True)
        raw_spans = parse_spans(content)
        pred = resolve_offsets(case["text"], raw_spans)
        gold = case["spans"]

        used = set()
        typed_tp = boundary = confusion = untyped_tp = 0
        missed: list[dict] = []
        for g in gold:
            best_ov = 0
            best_idx = -1
            for j, p_span in enumerate(pred):
                if j in used:
                    continue
                ov = overlap(g, p_span)
                if ov > best_ov:
                    best_ov = ov
                    best_idx = j
            if best_idx == -1 or best_ov == 0:
                missed.append(g)
                by_class_fn[g["label"]] = by_class_fn.get(g["label"], 0) + 1
                continue
            ps = pred[best_idx]
            used.add(best_idx)
            untyped_tp += 1
            if ps["label"] == g["label"] and ps["start"] == g["start"] and ps["end"] == g["end"]:
                typed_tp += 1
                by_class_tp[g["label"]] = by_class_tp.get(g["label"], 0) + 1
            elif ps["label"] == g["label"]:
                boundary += 1
                by_class_fn[g["label"]] = by_class_fn.get(g["label"], 0) + 1
                by_class_fp[ps["label"]] = by_class_fp.get(ps["label"], 0) + 1
            else:
                confusion += 1
                by_class_fn[g["label"]] = by_class_fn.get(g["label"], 0) + 1
                by_class_fp[ps["label"]] = by_class_fp.get(ps["label"], 0) + 1
        halluc = []
        for j, ps in enumerate(pred):
            if j not in used:
                halluc.append(ps)
                by_class_fp[ps["label"]] = by_class_fp.get(ps["label"], 0) + 1

        triages.append({
            "typed_tp": typed_tp, "untyped_tp": untyped_tp,
            "boundary": boundary, "confusion": confusion,
            "n_gold": len(gold), "n_pred": len(pred),
            "missed": missed, "hallucinated": halluc,
        })
        per_case.append({
            "id": case["id"], "register": case["register"],
            "n_gold": len(gold), "n_pred": len(pred),
            "typed_tp": typed_tp, "untyped_tp": untyped_tp,
            "boundary": boundary, "confusion": confusion,
            "missed": [{"label": s["label"], "text": s["text"]} for s in missed],
            "hallucinated": [{"label": s["label"], "text": s["text"]} for s in halluc],
        })

        if (i + 1) % 10 == 0:
            elapsed = time.time() - t_start
            print(f"[mini-hf] {i+1}/{len(cases)} ({elapsed:.1f}s)", flush=True)

    elapsed = time.time() - t_start

    typed_tp = sum(t["typed_tp"] for t in triages)
    untyped_tp = sum(t["untyped_tp"] for t in triages)
    boundary = sum(t["boundary"] for t in triages)
    confusion = sum(t["confusion"] for t in triages)
    n_gold = sum(t["n_gold"] for t in triages)
    n_pred = sum(t["n_pred"] for t in triages)
    n_missed = sum(len(t["missed"]) for t in triages)
    n_halluc = sum(len(t["hallucinated"]) for t in triages)

    typed_p = typed_tp / n_pred if n_pred else 0.0
    typed_r = typed_tp / n_gold if n_gold else 0.0
    typed_f1 = 2 * typed_p * typed_r / (typed_p + typed_r) if (typed_p + typed_r) else 0.0
    untyped_p = untyped_tp / n_pred if n_pred else 0.0
    untyped_r = untyped_tp / n_gold if n_gold else 0.0
    untyped_f1 = 2 * untyped_p * untyped_r / (untyped_p + untyped_r) if (untyped_p + untyped_r) else 0.0

    aggregate = {
        "n_cases": len(cases), "n_gold": n_gold, "n_pred": n_pred,
        "typed":   {"tp": typed_tp, "precision": typed_p, "recall": typed_r, "f1": typed_f1},
        "untyped": {"tp": untyped_tp, "precision": untyped_p, "recall": untyped_r, "f1": untyped_f1},
        "boundary_errors": boundary, "confusion_errors": confusion,
        "missed": n_missed, "hallucinated": n_halluc,
        "elapsed_seconds": elapsed,
    }

    by_class: dict = {}
    all_classes = set(by_class_tp) | set(by_class_fn) | set(by_class_fp)
    for cls in sorted(all_classes):
        tp = by_class_tp.get(cls, 0)
        fp = by_class_fp.get(cls, 0)
        fn = by_class_fn.get(cls, 0)
        p_ = tp / (tp + fp) if (tp + fp) else 0.0
        r_ = tp / (tp + fn) if (tp + fn) else 0.0
        f1_ = 2 * p_ * r_ / (p_ + r_) if (p_ + r_) else 0.0
        by_class[cls] = {"tp": tp, "fp": fp, "fn": fn, "precision": p_, "recall": r_, "f1": f1_}

    results = {
        "benchmark": str(args.benchmark),
        "models": {
            "mini_v3": {
                "checkpoint": str(args.lora_adapter),
                "aggregate": aggregate,
                "by_class": by_class,
                "per_case": per_case,
            }
        }
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {args.output}")
    print(f"  untyped F1 = {untyped_f1:.4f}  typed F1 = {typed_f1:.4f}  ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
