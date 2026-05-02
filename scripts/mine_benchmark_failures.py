from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRIAGE = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_triage_v2_12.json"
DEFAULT_JSON_OUT = PROJECT_ROOT / "artifacts" / "metrics" / "failure_mining_v2_12.json"
DEFAULT_MD_OUT = PROJECT_ROOT / "artifacts" / "metrics" / "failure_mining_v2_12.md"


def _f1(tp: int, boundary: int, confusion: int, missed: int, hallucinated: int) -> dict:
    fp = boundary + confusion + hallucinated
    fn = boundary + confusion + missed
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def _context(text: str, start: int, end: int, window: int = 42) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return text[left:right].replace("\n", "\\n")


def _best_decoder(results: dict) -> str:
    return max(results, key=lambda key: results[key]["aggregate"]["f1"])


def _pack_hint(label: str, issue: str, confusion_to: str | None = None) -> str:
    if label == "private_person":
        return "qwen_narrative/person_vocative_polytonic: surnames, vocatives, titles, two-person messages"
    if label == "private_email":
        return "qwen_contrastive/email_vs_secret: normal email plus adjacent token/key-like strings"
    if label == "private_phone":
        return "qwen_contrastive/phone_vs_account: phone markers and account markers in the same record"
    if label == "mac_address":
        return "qwen_contrastive/mac_vs_ip_vs_vin: network logs with MAC, IP, VIN-like device ids"
    if label in {"amka", "afm", "ama", "driver_license"}:
        return f"qwen_narrative/{label}_administrative: dense Greek admin prose with nearby numeric confusables"
    if label in {"ip_address", "imei", "card_pan", "cvv"}:
        return f"qwen_contrastive/{label}_technical_or_payment: same-record positive plus numeric confusable"
    if issue == "boundary":
        return "boundary_repair: include punctuation, honorifics, casing, and adjacent Greek words"
    if confusion_to:
        return f"contrastive: same record contains {label} and {confusion_to} with explicit local context"
    return "small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate"


def mine(payload: dict, decoder: str | None) -> dict:
    chosen = decoder or _best_decoder(payload["results"])
    result = payload["results"][chosen]
    aggregate = result["aggregate"]
    per_case = result["per_case"]

    class_rows: dict[str, dict] = {}
    all_classes = sorted(
        set(aggregate.get("per_class_tp", {}))
        | set(aggregate.get("per_class_boundary", {}))
        | set(aggregate.get("per_class_confusion", {}))
        | set(aggregate.get("per_class_missed", {}))
        | set(aggregate.get("per_class_halluc", {}))
    )
    for label in all_classes:
        tp = aggregate.get("per_class_tp", {}).get(label, 0)
        boundary = aggregate.get("per_class_boundary", {}).get(label, 0)
        confusion = aggregate.get("per_class_confusion", {}).get(label, 0)
        missed = aggregate.get("per_class_missed", {}).get(label, 0)
        hallucinated = aggregate.get("per_class_halluc", {}).get(label, 0)
        metrics = _f1(tp, boundary, confusion, missed, hallucinated)
        class_rows[label] = {
            "tp": tp,
            "boundary": boundary,
            "confusion": confusion,
            "missed": missed,
            "hallucinated": hallucinated,
            **metrics,
            "loss_events": boundary + confusion + missed + hallucinated,
        }

    missed_examples: dict[str, list[dict]] = defaultdict(list)
    boundary_examples: dict[str, list[dict]] = defaultdict(list)
    hallucinated_examples: dict[str, list[dict]] = defaultdict(list)
    confusion_pairs: Counter = Counter()
    confusion_examples: dict[str, list[dict]] = defaultdict(list)

    for case in per_case:
        text = case["text"]
        triage = case["triage"]
        for expected in triage["missed"]:
            label = expected["label"]
            missed_examples[label].append(
                {
                    "case_id": case["case_id"],
                    "register": case["register"],
                    "text": expected["text"],
                    "context": _context(text, expected["start"], expected["end"]),
                }
            )
        for predicted in triage["hallucinated"]:
            label = predicted["label"]
            hallucinated_examples[label].append(
                {
                    "case_id": case["case_id"],
                    "register": case["register"],
                    "text": predicted["text"],
                    "context": _context(text, predicted["start"], predicted["end"]),
                }
            )
        for pred_idx, exp_idx, ratio in triage["boundary_pairs"]:
            expected = case["expected"][exp_idx]
            predicted = case["predicted"][pred_idx]
            label = expected["label"]
            boundary_examples[label].append(
                {
                    "case_id": case["case_id"],
                    "register": case["register"],
                    "expected": expected["text"],
                    "predicted": predicted["text"],
                    "overlap_ratio": ratio,
                    "context": _context(text, expected["start"], expected["end"]),
                }
            )
        for pred_idx, exp_idx, ratio in triage["confusion_pairs"]:
            expected = case["expected"][exp_idx]
            predicted = case["predicted"][pred_idx]
            key = f"{expected['label']}->{predicted['label']}"
            confusion_pairs[key] += 1
            confusion_examples[key].append(
                {
                    "case_id": case["case_id"],
                    "register": case["register"],
                    "expected_label": expected["label"],
                    "predicted_label": predicted["label"],
                    "expected": expected["text"],
                    "predicted": predicted["text"],
                    "overlap_ratio": ratio,
                    "context": _context(text, expected["start"], expected["end"]),
                }
            )

    priorities = []
    for label, row in class_rows.items():
        missed = row["missed"]
        confusion = row["confusion"]
        boundary = row["boundary"]
        hallucinated = row["hallucinated"]
        priority_score = missed * 3 + confusion * 3 + boundary * 2 + hallucinated
        if priority_score == 0:
            continue
        top_confusion = None
        for pair, _ in confusion_pairs.most_common():
            src, dst = pair.split("->", 1)
            if src == label:
                top_confusion = dst
                break
        priorities.append(
            {
                "label": label,
                "priority_score": priority_score,
                "f1": row["f1"],
                "precision": row["precision"],
                "recall": row["recall"],
                "missed": missed,
                "confusion": confusion,
                "boundary": boundary,
                "hallucinated": hallucinated,
                "top_confusion": top_confusion,
                "recommended_pack": _pack_hint(label, "priority", top_confusion),
            }
        )
    priorities.sort(key=lambda item: (-item["priority_score"], item["f1"], item["label"]))

    return {
        "checkpoint": payload.get("checkpoint"),
        "decoder": chosen,
        "aggregate": aggregate,
        "class_metrics": class_rows,
        "priorities": priorities,
        "confusion_pairs": dict(confusion_pairs.most_common()),
        "examples": {
            "missed": {k: v[:8] for k, v in missed_examples.items()},
            "boundary": {k: v[:8] for k, v in boundary_examples.items()},
            "hallucinated": {k: v[:8] for k, v in hallucinated_examples.items()},
            "confusion": {k: v[:8] for k, v in confusion_examples.items()},
        },
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Benchmark Failure Mining",
        "",
        f"- Checkpoint: `{report.get('checkpoint')}`",
        f"- Decoder: `{report['decoder']}`",
        f"- Aggregate F1: `{report['aggregate']['f1']:.4f}`",
        f"- Precision / recall: `{report['aggregate']['precision']:.4f}` / `{report['aggregate']['recall']:.4f}`",
        "",
        "## Priorities",
        "",
        "| label | score | F1 | P | R | missed | confusion | boundary | hallucinated | pack |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in report["priorities"]:
        lines.append(
            "| {label} | {priority_score} | {f1:.3f} | {precision:.3f} | {recall:.3f} | "
            "{missed} | {confusion} | {boundary} | {hallucinated} | {recommended_pack} |".format(
                **item
            )
        )

    lines.extend(["", "## Top Confusions", ""])
    for pair, count in list(report["confusion_pairs"].items())[:20]:
        lines.append(f"- `{pair}`: {count}")

    lines.extend(["", "## Example Misses", ""])
    for label, examples in report["examples"]["missed"].items():
        lines.append(f"### {label}")
        for example in examples[:5]:
            lines.append(
                f"- case `{example['case_id']}` / `{example['register']}`: "
                f"`{example['text']}` in `{example['context']}`"
            )
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mine OPF benchmark triage JSON into ranked data-pack priorities."
    )
    parser.add_argument("--triage", type=Path, default=DEFAULT_TRIAGE)
    parser.add_argument("--decoder", default=None, help="Decoder key. Defaults to best F1.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.triage.read_text(encoding="utf-8"))
    report = mine(payload, args.decoder)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, args.md_out)
    print(f"JSON report: {args.json_out}")
    print(f"Markdown report: {args.md_out}")
    print("Top priorities:")
    for item in report["priorities"][:8]:
        print(
            f"- {item['label']}: score={item['priority_score']} "
            f"F1={item['f1']:.3f} R={item['recall']:.3f} "
            f"pack={item['recommended_pack']}"
        )


if __name__ == "__main__":
    main()
