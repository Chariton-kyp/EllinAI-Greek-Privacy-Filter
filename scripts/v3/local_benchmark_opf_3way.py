"""Run the Greek PII Public Benchmark v1 against 3 OPF-based models locally:
  - opf_base   (openai/privacy-filter, English-trained baseline)
  - v2_13      (12-class Greek fine-tune, 0.99 in-dist)
  - v3_lite    (24-class distilled, 0.99 in-dist / 0.78 OOD raw)

Uses the same OPF inference path for all three (since they share the
privacy-filter architecture). Runs predictions, computes per-case +
per-class + aggregate metrics in both:
  - typed   (exact label match) — fair only for v2_13/v3_lite
  - untyped (span detection only) — fair across all 3

Output: artifacts/metrics/benchmark_3way_opf.json

Usage:
    python scripts/v3/local_benchmark_opf_3way.py \\
        --benchmark benchmarks/greek_pii_public_v1/cases.jsonl \\
        --output artifacts/metrics/benchmark_3way_opf.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "greek_pii_public_v1" / "cases.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_3way_opf.json"

MODELS = {
    "opf_base":  PROJECT_ROOT / "checkpoints" / "base" / "privacy-filter",
    "v2_13":     PROJECT_ROOT / "artifacts" / "finetune-v2-13-20260501T202431Z" / "model",
    "v3_lite":   PROJECT_ROOT / "artifacts" / "v3" / "students" / "lite-v3-local",
}


def overlap(a: dict, b: dict) -> int:
    return max(0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def triage(gold: list[dict], pred: list[dict]) -> dict:
    """Match gold ↔ predicted spans by best overlap. Categorise each pair."""
    used_pred: set[int] = set()
    typed_tp = boundary = confusion = 0
    untyped_tp = 0
    missed: list[dict] = []
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
            typed_tp += 1
        elif same_label:
            boundary += 1
        else:
            confusion += 1
        # Untyped TP = any overlapping pair
        untyped_tp += 1
    halluc = [pred[i] for i in range(len(pred)) if i not in used_pred]
    return {
        "typed_tp": typed_tp,
        "boundary": boundary,
        "confusion": confusion,
        "untyped_tp": untyped_tp,
        "missed": missed,
        "hallucinated": halluc,
        "n_gold": len(gold),
        "n_pred": len(pred),
    }


def aggregate_metrics(triages: list[dict]) -> dict:
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

    return {
        "n_cases": len(triages),
        "n_gold": n_gold,
        "n_pred": n_pred,
        "typed":   {"tp": typed_tp, "precision": typed_p, "recall": typed_r, "f1": typed_f1},
        "untyped": {"tp": untyped_tp, "precision": untyped_p, "recall": untyped_r, "f1": untyped_f1},
        "boundary_errors": boundary,
        "confusion_errors": confusion,
        "missed": n_missed,
        "hallucinated": n_halluc,
    }


def per_class_breakdown(triages: list[dict], cases: list[dict]) -> dict:
    """Compute typed F1 per class. For each gold class, count tp/fp/fn."""
    by_class_tp: Counter = Counter()
    by_class_fn: Counter = Counter()
    by_class_fp: Counter = Counter()
    # Need to recompute matching per class
    for case, t in zip(cases, triages):
        gold = case["spans"]
        pred = [
            *t.get("_pred_full", [])  # filled below if we keep raw pred
        ]
    # Lighter approach: recompute on the fly using triage outputs
    # For each triage:
    #   typed_tp pairs are matched (label+offset) — count by gold label
    #   missed are by gold label only (FN)
    #   hallucinated are by pred label only (FP)
    #   boundary/confusion: count as FN of gold label + FP of pred label (typed mismatch)
    return {}  # filled by caller (we'll count at evaluation time)


def load_model(name: str, checkpoint: Path):
    """Load OPF model from checkpoint dir."""
    print(f"[{name}] loading {checkpoint}", flush=True)
    if not checkpoint.exists():
        raise FileNotFoundError(f"checkpoint dir not found: {checkpoint}")
    # OPF API
    from opf import OPF  # type: ignore
    detector = OPF(model=str(checkpoint), device="cuda")
    return detector


def predict_all(detector, cases: list[dict], model_name: str) -> tuple[list[list[dict]], float]:
    """Run model.redact over all cases. Return (per-case predictions, elapsed_s)."""
    out: list[list[dict]] = []
    t0 = time.time()
    for i, case in enumerate(cases):
        try:
            res = detector.redact(case["text"])
            spans = []
            for s in res.detected_spans:
                spans.append({
                    "label": getattr(s, "label", "UNKNOWN"),
                    "start": int(s.start),
                    "end": int(s.end),
                    "text": case["text"][int(s.start):int(s.end)],
                })
            out.append(spans)
        except Exception as e:
            print(f"[{model_name}] case {case['id']} FAIL: {e}", flush=True)
            out.append([])
        if (i + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"[{model_name}] {i+1}/{len(cases)} ({elapsed:.1f}s)", flush=True)
    elapsed = time.time() - t0
    return out, elapsed


def evaluate_model(name: str, checkpoint: Path, cases: list[dict]) -> dict:
    detector = load_model(name, checkpoint)
    predictions, elapsed = predict_all(detector, cases, name)
    triages: list[dict] = []
    by_class_tp: Counter = Counter()
    by_class_fn: Counter = Counter()
    by_class_fp: Counter = Counter()
    for case, pred in zip(cases, predictions):
        gold = case["spans"]
        t = triage(gold, pred)
        triages.append(t)
        # Per-class typed: tp = label+offset match
        # Match again by best overlap (same algorithm as triage, but track labels)
        used = set()
        for g in gold:
            best_ov = 0
            best_idx = -1
            for i, p in enumerate(pred):
                if i in used:
                    continue
                ov = overlap(g, p)
                if ov > best_ov:
                    best_ov = ov
                    best_idx = i
            if best_idx == -1 or best_ov == 0:
                by_class_fn[g["label"]] += 1
                continue
            p = pred[best_idx]
            used.add(best_idx)
            if p["label"] == g["label"] and p["start"] == g["start"] and p["end"] == g["end"]:
                by_class_tp[g["label"]] += 1
            elif p["label"] == g["label"]:
                # boundary mismatch — treat as FN of g and FP of p (same label)
                by_class_fn[g["label"]] += 1
                by_class_fp[p["label"]] += 1
            else:
                by_class_fn[g["label"]] += 1
                by_class_fp[p["label"]] += 1
        for i, p in enumerate(pred):
            if i not in used:
                by_class_fp[p["label"]] += 1

    by_class: dict = {}
    all_classes = set(by_class_tp) | set(by_class_fn) | set(by_class_fp)
    for cls in sorted(all_classes):
        tp = by_class_tp.get(cls, 0)
        fp = by_class_fp.get(cls, 0)
        fn = by_class_fn.get(cls, 0)
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        by_class[cls] = {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}

    aggregate = aggregate_metrics(triages)
    aggregate["elapsed_seconds"] = elapsed

    # Strip massive missed/hallucinated arrays from per-case for JSON size
    per_case = []
    for case, t in zip(cases, triages):
        per_case.append({
            "id": case["id"],
            "register": case["register"],
            "n_gold": t["n_gold"],
            "n_pred": t["n_pred"],
            "typed_tp": t["typed_tp"],
            "untyped_tp": t["untyped_tp"],
            "boundary": t["boundary"],
            "confusion": t["confusion"],
            "missed": [{"label": s["label"], "text": s["text"]} for s in t["missed"]],
            "hallucinated": [{"label": s["label"], "text": s["text"]} for s in t["hallucinated"]],
        })

    return {
        "checkpoint": str(checkpoint),
        "aggregate": aggregate,
        "by_class": by_class,
        "per_case": per_case,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--models", nargs="*", default=list(MODELS.keys()),
                    help="Subset of models to evaluate.")
    args = p.parse_args()

    # Load benchmark
    cases: list[dict] = []
    with args.benchmark.open(encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))
    print(f"loaded {len(cases)} cases from {args.benchmark}", flush=True)

    results: dict = {"benchmark": str(args.benchmark), "models": {}}

    for name in args.models:
        if name not in MODELS:
            print(f"WARN: unknown model {name}, skipping", flush=True)
            continue
        ckpt = MODELS[name]
        try:
            results["models"][name] = evaluate_model(name, ckpt, cases)
        except Exception as e:
            print(f"[{name}] FATAL: {e}", flush=True)
            results["models"][name] = {"error": str(e)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {args.output}")

    print("\n=== Summary (untyped F1 / typed F1) ===")
    for name, r in results["models"].items():
        if "error" in r:
            print(f"  {name:<10s}  ERROR: {r['error']}")
            continue
        a = r["aggregate"]
        print(f"  {name:<10s}  untyped F1 = {a['untyped']['f1']:.4f}  "
              f"typed F1 = {a['typed']['f1']:.4f}  "
              f"({a['elapsed_seconds']:.1f}s)")


if __name__ == "__main__":
    main()
