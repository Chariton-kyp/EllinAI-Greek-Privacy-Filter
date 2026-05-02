"""Run all v3 tiers (causal-LM students + Lite token-classifier) on the
locked 200-case OOD benchmark and emit one comparison table.

For causal-LM tiers (mini/pro/max/ultra/teacher), the model is queried
in JSON-spans mode via an OpenAI-compatible endpoint. Each prediction
is parsed → resolved to char offsets → scored against the gold OPF
spans using the same triage logic as the existing benchmark harness.

For the Lite tier (privacy-filter 1.4B token-classifier), we just
delegate to the existing scripts/run_benchmark_triage.py.

Usage:
    python scripts/v3/benchmark_tiers.py \\
        --benchmark data/realworld_benchmark/cases.jsonl \\
        --tiers '[
            {"name":"lite","kind":"opf-token-classifier","checkpoint":"artifacts/finetune-v2-13-.../model"},
            {"name":"mini","kind":"causal-lm","host":"http://127.0.0.1:8080","model":"gemma4-e2b"},
            {"name":"pro", "kind":"causal-lm","host":"http://127.0.0.1:8081","model":"gemma4-e4b"},
            {"name":"max", "kind":"causal-lm","host":"http://127.0.0.1:8082","model":"qwen3-4b"},
            {"name":"ultra","kind":"causal-lm","host":"http://127.0.0.1:8083","model":"gemma4-31b"}
        ]' \\
        --output artifacts/metrics/benchmark_v3_tiers.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


SYSTEM_PROMPT = (
    "Είσαι σύστημα ανίχνευσης ευαίσθητων προσωπικών δεδομένων (PII) σε "
    "ελληνικό κείμενο. Όταν σου δίνεται ένα κείμενο, απαντάς ΑΠΟΚΛΕΙΣΤΙΚΑ "
    "με μια έγκυρη JSON λίστα της μορφής:\n"
    "  [{\"label\": \"<class>\", \"value\": \"<αυτούσιο απόσπασμα>\"}, ...]\n"
    "Αν δεν υπάρχει κανένα PII, απάντησε []. ΟΧΙ σχόλια, ΟΧΙ markdown."
)
_JSON_LIST_RE = re.compile(r"\[\s*(?:\{.*?\})?\s*(?:,\s*\{.*?\}\s*)*\]", re.DOTALL)


def call_openai(host: str, model: str, user_prompt: str) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/v1/chat/completions",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]


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
    out = []
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


def triage(gold: list[dict], pred: list[dict]) -> dict:
    """Match gold ↔ predicted spans. Same logic as run_benchmark_triage.py."""
    used_pred = set()
    tp = b = c = 0
    missed = []
    for g in gold:
        best_ov = 0
        best_idx = -1
        for i, p in enumerate(pred):
            if i in used_pred:
                continue
            ov = overlap(g, p)
            if ov > best_ov:
                best_ov = ov
                best_idx = i
        if best_idx == -1 or best_ov == 0:
            missed.append(g)
            continue
        p = pred[best_idx]
        used_pred.add(best_idx)
        same_label = p["label"] == g["label"]
        same_offsets = (p["start"] == g["start"] and p["end"] == g["end"])
        if same_label and same_offsets:
            tp += 1
        elif same_label:
            b += 1
        else:
            c += 1
    halluc = [pred[i] for i in range(len(pred)) if i not in used_pred]
    return {
        "tp": tp,
        "boundary": b,
        "confusion": c,
        "missed": missed,
        "hallucinated": halluc,
    }


def aggregate(triages: list[dict]) -> dict:
    tp = sum(t["tp"] for t in triages)
    b = sum(t["boundary"] for t in triages)
    c = sum(t["confusion"] for t in triages)
    m = sum(len(t["missed"]) for t in triages)
    h = sum(len(t["hallucinated"]) for t in triages)
    gold = tp + b + c + m
    pred = tp + b + c + h
    p = tp / pred if pred else 0.0
    r = tp / gold if gold else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "boundary": b, "confusion": c, "missed": m,
            "hallucinated": h, "precision": p, "recall": r, "f1": f1}


def evaluate_causal_lm(tier: dict, cases: list[dict]) -> dict:
    triages = []
    for case in cases:
        try:
            content = call_openai(tier["host"], tier["model"], case["text"])
            spans = parse_spans(content)
            pred = resolve_offsets(case["text"], spans)
        except Exception as e:
            print(f"[{tier['name']}] case {case.get('case_id')} FAIL: {e}", flush=True)
            pred = []
        triages.append(triage(case.get("expected", case.get("spans", [])), pred))
    return aggregate(triages)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--benchmark", type=Path,
                    default=Path("data/realworld_benchmark/cases.jsonl"))
    p.add_argument("--tiers", required=True,
                    help="JSON list of {name, kind, host?, model?, checkpoint?}.")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    cases = []
    with args.benchmark.open(encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            # Normalise: spans → expected (use existing 'spans' field with start/end)
            spans = c.get("spans", [])
            c["expected"] = [{"label": s["label"], "start": s["start"], "end": s["end"]}
                              for s in spans]
            cases.append(c)
    print(f"loaded {len(cases)} benchmark cases", flush=True)

    tiers = json.loads(args.tiers)
    results = {}
    for tier in tiers:
        name = tier["name"]
        kind = tier["kind"]
        print(f"\n=== {name} ({kind}) ===", flush=True)
        t0 = time.time()
        if kind == "causal-lm":
            agg = evaluate_causal_lm(tier, cases)
        elif kind == "opf-token-classifier":
            print(f"[{name}] delegate to scripts/run_benchmark_triage.py manually; skipping",
                  flush=True)
            continue
        else:
            print(f"[{name}] unknown kind: {kind}", flush=True)
            continue
        agg["elapsed_seconds"] = time.time() - t0
        agg["tier"] = name
        agg["hf_id"] = tier.get("model", tier.get("checkpoint"))
        results[name] = agg
        print(f"  F1={agg['f1']:.4f}  P={agg['precision']:.4f}  R={agg['recall']:.4f}  "
              f"TP={agg['tp']} M={agg['missed']} H={agg['hallucinated']}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
