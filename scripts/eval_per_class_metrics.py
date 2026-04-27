"""Per-class span-level evaluation harness for OPF-format JSONL splits.

Loads a fine-tuned OPF checkpoint, runs span detection over every
record in a JSONL split, and emits a per-class metrics report that
covers what `python -m opf eval` produces plus three breakdowns the
upstream tool does not:

1. Per-class confusion matrix — counts of (gold-class, predicted-class)
   pairs over spans whose boundaries overlap, so you can see at a
   glance that, say, ``afm`` predictions cross-confuse with
   ``account_number`` rather than ``private_phone``.
2. Boundary-error categorisation — for every false negative and
   false positive, classifies the error as one of: missed (no
   overlapping prediction at all), wrong_class (overlapping
   prediction with a different label), wrong_boundary (overlapping
   prediction with the same label but different start/end),
   hallucinated (predicted span with no gold span overlapping).
3. Per-class span counts — gold-positive count and predicted-positive
   count side by side, so the per-class precision/recall numbers are
   easier to interpret in low-support classes.

Span-level matching is exact: a true positive requires
(gold.label, gold.start, gold.end) == (pred.label, pred.start,
pred.end).

Usage:

    python scripts/eval_per_class_metrics.py \\
        --checkpoint data/processed/aws-ft-20260426T135853Z/model \\
        --split data/processed/v1_1/test.jsonl \\
        --output artifacts/metrics/per_class_eval_v1_1_test.json \\
        --device cuda

Writes a JSON report; prints a compact summary to stdout. Exit code
non-zero if any span-level F1 falls below ``--min-f1`` (default 0,
i.e. no gating). Useful in a launcher to gate v2 retrains on the
relabelled splits.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ClassStats:
    """Per-class counters."""

    gold_count: int = 0
    pred_count: int = 0
    true_positives: int = 0
    # Errors observed against this class's gold spans:
    missed: int = 0
    wrong_class: int = 0  # overlapping pred but different label
    wrong_boundary: int = 0  # overlapping pred, same label, different boundaries
    # Errors observed against this class's predictions:
    hallucinated: int = 0  # pred span with no overlapping gold


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """True if spans [a_start, a_end) and [b_start, b_end) share any
    character."""
    return a_start < b_end and b_start < a_end


def categorise_errors(
    gold_spans: list[dict],
    pred_spans: list[dict],
    class_stats: dict[str, ClassStats],
    confusion: dict[tuple[str, str], int],
) -> None:
    """Update class_stats and confusion_matrix in place.

    A true positive is exact (label, start, end) match.
    A wrong_boundary error is overlapping with same label but
    different boundaries.
    A wrong_class error is overlapping with a different label.
    A missed error is a gold span with no overlapping prediction.
    A hallucinated error is a prediction with no overlapping gold.
    """
    used_pred = [False] * len(pred_spans)

    for gs in gold_spans:
        gl, gst, gen = gs["label"], gs["start"], gs["end"]
        class_stats[gl].gold_count += 1
        # Look for an exact match first.
        exact = -1
        for i, ps in enumerate(pred_spans):
            if used_pred[i]:
                continue
            if (
                ps["label"] == gl
                and ps["start"] == gst
                and ps["end"] == gen
            ):
                exact = i
                break
        if exact >= 0:
            used_pred[exact] = True
            class_stats[gl].true_positives += 1
            confusion[(gl, gl)] = confusion.get((gl, gl), 0) + 1
            continue
        # No exact; look for an overlapping prediction.
        overlap_idx = -1
        for i, ps in enumerate(pred_spans):
            if used_pred[i]:
                continue
            if overlaps(gst, gen, ps["start"], ps["end"]):
                overlap_idx = i
                break
        if overlap_idx >= 0:
            used_pred[overlap_idx] = True
            ps = pred_spans[overlap_idx]
            if ps["label"] == gl:
                class_stats[gl].wrong_boundary += 1
                confusion[(gl, gl + "*boundary")] = (
                    confusion.get((gl, gl + "*boundary"), 0) + 1
                )
            else:
                class_stats[gl].wrong_class += 1
                confusion[(gl, ps["label"])] = (
                    confusion.get((gl, ps["label"]), 0) + 1
                )
        else:
            class_stats[gl].missed += 1
            confusion[(gl, "(missed)")] = confusion.get((gl, "(missed)"), 0) + 1

    # Hallucinations: any prediction not yet matched.
    for i, ps in enumerate(pred_spans):
        if used_pred[i]:
            continue
        pl = ps["label"]
        class_stats[pl].pred_count += 1
        class_stats[pl].hallucinated += 1
        confusion[("(hallucinated)", pl)] = (
            confusion.get(("(hallucinated)", pl), 0) + 1
        )

    # All matched preds also count toward pred_count.
    for i, ps in enumerate(pred_spans):
        if used_pred[i]:
            class_stats[ps["label"]].pred_count += 1


def precision_recall_f1(
    tp: int, pred: int, gold: int
) -> tuple[float, float, float]:
    p = tp / pred if pred else 0.0
    r = tp / gold if gold else 0.0
    if p + r == 0:
        return p, r, 0.0
    return p, r, 2 * p * r / (p + r)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--checkpoint",
        default=os.environ.get("OPF_CHECKPOINT_DIR"),
        help=(
            "Directory containing the fine-tuned OPF checkpoint. Falls "
            "back to $OPF_CHECKPOINT_DIR. No default — pass explicitly."
        ),
    )
    parser.add_argument(
        "--split",
        type=Path,
        required=True,
        help="Path to the OPF-format JSONL split to evaluate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "artifacts"
        / "metrics"
        / "per_class_eval.json",
        help="Path to write the per-class metrics JSON report.",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("OPF_DEVICE", "cuda"),
        choices=["cuda", "cpu"],
        help="Inference device. Defaults to cuda.",
    )
    parser.add_argument(
        "--min-f1",
        type=float,
        default=0.0,
        help=(
            "If > 0, exit non-zero when any class's span F1 falls below "
            "this value. Useful for gating launcher / CI runs."
        ),
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help=(
            "Only evaluate the first N records of the split. Useful "
            "for smoke checks; omit for full evaluation."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.checkpoint:
        print(
            "FAIL: --checkpoint required (or set $OPF_CHECKPOINT_DIR).",
            file=sys.stderr,
        )
        return 1
    checkpoint_dir = Path(args.checkpoint).expanduser().resolve()
    split_path = args.split.expanduser().resolve()
    if not checkpoint_dir.exists():
        print(f"FAIL: checkpoint dir not found: {checkpoint_dir}", file=sys.stderr)
        return 1
    if not split_path.is_file():
        print(f"FAIL: split not found: {split_path}", file=sys.stderr)
        return 1

    print(f"[load] checkpoint = {checkpoint_dir}")
    print(f"[load] split      = {split_path}")
    print(f"[load] device     = {args.device}")
    from opf import OPF  # type: ignore[import-not-found]

    detector = OPF(model=str(checkpoint_dir), device=args.device)
    print("[load] model ready")

    class_stats: dict[str, ClassStats] = defaultdict(ClassStats)
    confusion: dict[tuple[str, str], int] = {}
    record_total = 0
    skipped = 0
    with split_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            if args.max_records is not None and record_total >= args.max_records:
                break
            record_total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            text = record["text"]
            gold_spans = [
                {"label": lab["category"], "start": int(lab["start"]), "end": int(lab["end"])}
                for lab in record.get("label", [])
            ]
            result = detector.redact(text)
            pred_spans = [
                {"label": s.label, "start": int(s.start), "end": int(s.end)}
                for s in result.detected_spans
            ]
            categorise_errors(gold_spans, pred_spans, class_stats, confusion)
            if record_total % 200 == 0:
                print(f"  ...{record_total} records evaluated")

    # Compose report.
    per_class_out: dict[str, dict] = {}
    overall_tp = 0
    overall_pred = 0
    overall_gold = 0
    min_class_f1 = (None, 1.0)
    for cls in sorted(class_stats):
        s = class_stats[cls]
        p, r, f = precision_recall_f1(s.true_positives, s.pred_count, s.gold_count)
        per_class_out[cls] = {
            "gold_count": s.gold_count,
            "pred_count": s.pred_count,
            "true_positives": s.true_positives,
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
            "missed": s.missed,
            "wrong_class": s.wrong_class,
            "wrong_boundary": s.wrong_boundary,
            "hallucinated": s.hallucinated,
        }
        overall_tp += s.true_positives
        overall_pred += s.pred_count
        overall_gold += s.gold_count
        if s.gold_count > 0 and f < min_class_f1[1]:
            min_class_f1 = (cls, f)

    op, orr, of = precision_recall_f1(overall_tp, overall_pred, overall_gold)

    confusion_out: list[dict] = []
    for (gold_cls, pred_cls), n in sorted(
        confusion.items(), key=lambda kv: -kv[1]
    ):
        confusion_out.append(
            {"gold": gold_cls, "predicted": pred_cls, "count": n}
        )

    report = {
        "checkpoint": str(checkpoint_dir),
        "split": str(split_path),
        "device": args.device,
        "records_evaluated": record_total,
        "records_skipped": skipped,
        "overall": {
            "gold_count": overall_gold,
            "pred_count": overall_pred,
            "true_positives": overall_tp,
            "precision": round(op, 4),
            "recall": round(orr, 4),
            "f1": round(of, 4),
        },
        "per_class": per_class_out,
        "confusion_matrix": confusion_out,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print()
    print("=== Per-class span-level metrics ===")
    print(
        f"  {'class':<18s} {'gold':>6s} {'pred':>6s} {'TP':>6s} "
        f"{'P':>6s} {'R':>6s} {'F1':>6s}"
    )
    for cls, m in per_class_out.items():
        print(
            f"  {cls:<18s} {m['gold_count']:>6d} {m['pred_count']:>6d} "
            f"{m['true_positives']:>6d} "
            f"{m['precision']:>6.4f} {m['recall']:>6.4f} {m['f1']:>6.4f}"
        )
    print()
    print(
        f"OVERALL: gold={overall_gold} pred={overall_pred} TP={overall_tp} "
        f"P={op:.4f} R={orr:.4f} F1={of:.4f}"
    )
    print(f"  full report: {args.output}")

    if args.min_f1 > 0 and min_class_f1[0] is not None and min_class_f1[1] < args.min_f1:
        print(
            f"FAIL: lowest class F1 = {min_class_f1[1]:.4f} on {min_class_f1[0]} "
            f"falls below --min-f1 {args.min_f1:.4f}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
