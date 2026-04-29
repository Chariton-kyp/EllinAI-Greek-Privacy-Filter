"""Run the locked 200-case benchmark against an OPF checkpoint with
multiple decoder variants and triage failures.

Decoder variants compared:
  - viterbi (default)
  - argmax
  - viterbi + discard_overlapping=True

Failures categorized into:
  - boundary  : predicted span overlaps (>=50% chars) with an expected
                span of the same label, but offsets differ.
  - confusion : predicted span overlaps an expected span at a different
                label.
  - missed    : expected span has no predicted span overlap.
  - hallucination : predicted span has no expected span overlap.

Output:
  artifacts/metrics/benchmark_triage.json  — full per-case payload
  Console table summary per decoder + per-class breakdown.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT = (
    PROJECT_ROOT / "artifacts" / "finetune-v2-20260428T134618Z" / "model"
)
DEFAULT_BENCHMARK = PROJECT_ROOT / "data" / "realworld_benchmark" / "cases.jsonl"


def load_cases(path: Path) -> list[dict]:
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))
    return cases


def overlap_ratio(span_a: dict, span_b: dict) -> float:
    """Return char-overlap ratio between two spans (relative to shorter span)."""
    a0, a1 = span_a["start"], span_a["end"]
    b0, b1 = span_b["start"], span_b["end"]
    overlap = max(0, min(a1, b1) - max(a0, b0))
    if overlap == 0:
        return 0.0
    shorter = min(a1 - a0, b1 - b0)
    return overlap / shorter if shorter else 0.0


def classify_predictions(
    expected: list[dict], predicted: list[dict]
) -> dict[str, list]:
    """Match predicted vs expected; classify each into TP / boundary /
    confusion / missed / hallucinated."""
    matched_expected = set()
    matched_predicted = set()

    tp_pairs = []
    boundary_pairs = []
    confusion_pairs = []

    for pi, p in enumerate(predicted):
        for ei, e in enumerate(expected):
            if ei in matched_expected:
                continue
            ratio = overlap_ratio(p, e)
            if ratio == 0:
                continue
            same_offsets = (p["start"] == e["start"] and p["end"] == e["end"])
            same_label = (p["label"] == e["label"])
            if same_offsets and same_label:
                tp_pairs.append((pi, ei))
                matched_expected.add(ei)
                matched_predicted.add(pi)
                break
            if ratio >= 0.5 and same_label:
                boundary_pairs.append((pi, ei, ratio))
                matched_expected.add(ei)
                matched_predicted.add(pi)
                break
            if ratio >= 0.5 and not same_label:
                confusion_pairs.append((pi, ei, ratio))
                matched_expected.add(ei)
                matched_predicted.add(pi)
                break

    missed = [e for ei, e in enumerate(expected) if ei not in matched_expected]
    hallucinated = [
        p for pi, p in enumerate(predicted) if pi not in matched_predicted
    ]
    tp = len(tp_pairs)
    return {
        "tp": tp,
        "tp_pairs": tp_pairs,
        "boundary_pairs": boundary_pairs,
        "confusion_pairs": confusion_pairs,
        "missed": missed,
        "hallucinated": hallucinated,
    }


def f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def run_decoder(redactor, cases: list[dict]) -> list[dict]:
    out = []
    for case in cases:
        result = redactor.redact(case["text"])
        predicted = []
        for s in result.detected_spans:
            label = s.label
            if label.startswith(("B-", "I-")):
                label = label[2:]
            predicted.append(
                {"label": label, "text": s.text, "start": s.start, "end": s.end}
            )
        cls = classify_predictions(case["spans"], predicted)
        out.append(
            {"case_id": case["id"], "register": case["register"],
             "text": case["text"], "expected": case["spans"],
             "predicted": predicted, "triage": cls}
        )
    return out


def aggregate(per_case: list[dict]) -> dict:
    total_tp = 0
    total_boundary = 0
    total_confusion = 0
    total_missed = 0
    total_halluc = 0
    per_class_tp = Counter()
    per_class_boundary = Counter()
    per_class_confusion = Counter()
    per_class_missed = Counter()
    per_class_halluc = Counter()
    for c in per_case:
        t = c["triage"]
        total_tp += t["tp"]
        total_boundary += len(t["boundary_pairs"])
        total_confusion += len(t["confusion_pairs"])
        total_missed += len(t["missed"])
        total_halluc += len(t["hallucinated"])
        for pi, ei in t["tp_pairs"]:
            per_class_tp[c["expected"][ei]["label"]] += 1
        for pi, ei, _ in t["boundary_pairs"]:
            per_class_boundary[c["expected"][ei]["label"]] += 1
        for pi, ei, _ in t["confusion_pairs"]:
            per_class_confusion[c["expected"][ei]["label"]] += 1
        for m in t["missed"]:
            per_class_missed[m["label"]] += 1
        for h in t["hallucinated"]:
            per_class_halluc[h["label"]] += 1
    fp = total_boundary + total_confusion + total_halluc
    fn = total_boundary + total_confusion + total_missed
    p, r, F = f1(total_tp, fp, fn)
    return {
        "tp": total_tp, "boundary": total_boundary, "confusion": total_confusion,
        "missed": total_missed, "hallucinated": total_halluc,
        "precision": p, "recall": r, "f1": F,
        "per_class_tp": dict(per_class_tp),
        "per_class_boundary": dict(per_class_boundary),
        "per_class_confusion": dict(per_class_confusion),
        "per_class_missed": dict(per_class_missed),
        "per_class_halluc": dict(per_class_halluc),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    p.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    p.add_argument(
        "--metrics-out",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_triage.json",
    )
    args = p.parse_args()

    ckpt = args.checkpoint or Path(
        os.environ.get("OPF_CHECKPOINT_DIR", str(DEFAULT_CHECKPOINT))
    )
    if not ckpt.exists():
        print(f"FAIL: checkpoint not found at {ckpt}", file=sys.stderr)
        sys.exit(1)

    cases = load_cases(args.benchmark)
    print(f"Loaded {len(cases)} cases from {args.benchmark}")
    print(f"Checkpoint: {ckpt}, device: {args.device}")

    sys.path.insert(0, str(PROJECT_ROOT / "external" / "privacy-filter"))
    from opf import OPF

    variants = [
        {"name": "viterbi", "decode_mode": "viterbi", "discard_overlap": False},
        {"name": "argmax", "decode_mode": "argmax", "discard_overlap": False},
        {"name": "viterbi_no_overlap", "decode_mode": "viterbi", "discard_overlap": True},
    ]

    all_results: dict[str, dict] = {}
    for v in variants:
        print(f"\n=== Running variant: {v['name']} ===")
        redactor = OPF(
            model=str(ckpt),
            device=args.device,
            output_mode="typed",
            decode_mode=v["decode_mode"],
            discard_overlapping_predicted_spans=v["discard_overlap"],
        )
        per_case = run_decoder(redactor, cases)
        agg = aggregate(per_case)
        all_results[v["name"]] = {"aggregate": agg, "per_case": per_case}
        print(
            f"  TP={agg['tp']} boundary={agg['boundary']} "
            f"confusion={agg['confusion']} missed={agg['missed']} "
            f"hallucinated={agg['hallucinated']}"
        )
        print(
            f"  precision={agg['precision']:.4f} "
            f"recall={agg['recall']:.4f} F1={agg['f1']:.4f}"
        )
        del redactor

    print("\n\n========== Decoder comparison ==========")
    print(f"{'variant':22s} {'F1':>7s} {'P':>7s} {'R':>7s} "
          f"{'TP':>5s} {'B':>4s} {'C':>4s} {'M':>4s} {'H':>4s}")
    for name, r in all_results.items():
        a = r["aggregate"]
        print(
            f"{name:22s} {a['f1']:>7.4f} {a['precision']:>7.4f} "
            f"{a['recall']:>7.4f} {a['tp']:>5d} {a['boundary']:>4d} "
            f"{a['confusion']:>4d} {a['missed']:>4d} {a['hallucinated']:>4d}"
        )

    print("\n========== Per-class triage (best variant) ==========")
    best = max(all_results, key=lambda k: all_results[k]["aggregate"]["f1"])
    print(f"Best decoder: {best}")
    a = all_results[best]["aggregate"]
    classes = sorted(
        set(a["per_class_tp"]) | set(a["per_class_boundary"])
        | set(a["per_class_confusion"]) | set(a["per_class_missed"])
        | set(a["per_class_halluc"])
    )
    print(f"{'class':22s} {'TP':>4s} {'B':>4s} {'C':>4s} {'M':>4s} {'H':>4s} {'F1':>7s}")
    for c in classes:
        tp_ = a["per_class_tp"].get(c, 0)
        b_ = a["per_class_boundary"].get(c, 0)
        cf_ = a["per_class_confusion"].get(c, 0)
        m_ = a["per_class_missed"].get(c, 0)
        h_ = a["per_class_halluc"].get(c, 0)
        fp = b_ + cf_ + h_
        fn = b_ + cf_ + m_
        _, _, fscore = f1(tp_, fp, fn)
        print(f"{c:22s} {tp_:>4d} {b_:>4d} {cf_:>4d} {m_:>4d} {h_:>4d} {fscore:>7.4f}")

    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.metrics_out, "w", encoding="utf-8") as f:
        json.dump({"checkpoint": str(ckpt), "results": all_results}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nFull report written: {args.metrics_out}")


if __name__ == "__main__":
    main()
