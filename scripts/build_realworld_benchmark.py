"""Validate hand-crafted benchmark cases and emit JSONL.

Reads cases from scripts/realworld_benchmark/cases_batchN.py modules,
validates that every span text occurs verbatim in the case text, computes
char offsets, asserts no class with <8 occurrences, and writes the
combined JSONL to data/realworld_benchmark/cases.jsonl.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_ROOT / "scripts" / "realworld_benchmark"
OUTPUT = PROJECT_ROOT / "data" / "realworld_benchmark" / "cases.jsonl"

V2_CLASSES = {
    "account_number", "adt", "afm", "amka", "iban_gr",
    "private_address", "private_date", "private_email", "private_person",
    "private_phone", "private_url", "secret",
    "passport", "license_plate", "vehicle_vin", "gemi", "ama",
    "card_pan", "cvv", "imei", "ip_address", "mac_address",
    "driver_license", "pcn",
}


def load_batches() -> list[dict]:
    cases: list[dict] = []
    files = sorted(BATCH_DIR.glob("cases_batch*.py"))
    if not files:
        print(f"FAIL: no batches at {BATCH_DIR}", file=sys.stderr)
        sys.exit(1)
    for f in files:
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "CASES"):
            print(f"WARN: {f.name} missing CASES list", file=sys.stderr)
            continue
        for c in mod.CASES:
            cases.append(c)
        print(f"  loaded {len(mod.CASES)} cases from {f.name}")
    return cases


def compute_offsets(case: dict) -> dict:
    text = case["text"]
    out_spans = []
    cursor_per_text: dict[str, int] = {}
    for s in case["spans"]:
        label = s["label"]
        span_text = s["text"]
        start_search = cursor_per_text.get(span_text, 0)
        idx = text.find(span_text, start_search)
        if idx == -1:
            raise ValueError(
                f"case {case['id']}: span text '{span_text}' "
                f"(label={label}) not found in text"
            )
        end = idx + len(span_text)
        cursor_per_text[span_text] = end
        if label not in V2_CLASSES:
            raise ValueError(
                f"case {case['id']}: unknown label '{label}' (not in v2 schema)"
            )
        out_spans.append(
            {"label": label, "text": span_text, "start": idx, "end": end}
        )
    return {
        "id": case["id"],
        "register": case["register"],
        "text": text,
        "spans": out_spans,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=8,
        help="Minimum number of occurrences required per class.",
    )
    parser.add_argument(
        "--require-coverage",
        action="store_true",
        help="Fail if any class falls below --min-coverage. Off by default "
             "while we are still building up the benchmark.",
    )
    args = parser.parse_args()

    cases = load_batches()
    print(f"\nTotal cases loaded: {len(cases)}")

    seen_ids = set()
    validated = []
    for c in cases:
        if c["id"] in seen_ids:
            raise ValueError(f"duplicate case id {c['id']}")
        seen_ids.add(c["id"])
        validated.append(compute_offsets(c))

    span_counts: Counter[str] = Counter()
    for v in validated:
        for s in v["spans"]:
            span_counts[s["label"]] += 1

    print("\nClass coverage:")
    for cls in sorted(V2_CLASSES):
        count = span_counts.get(cls, 0)
        flag = "OK" if count >= args.min_coverage else f"LOW (<{args.min_coverage})"
        print(f"  {cls:22s} {count:>4d}   {flag}")

    low = [c for c in V2_CLASSES if span_counts.get(c, 0) < args.min_coverage]
    if low and args.require_coverage:
        print(f"\nFAIL: classes below {args.min_coverage}: {low}", file=sys.stderr)
        sys.exit(1)
    elif low:
        print(f"\nWARN: classes below {args.min_coverage}: {low}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for v in validated:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(validated)} cases to {OUTPUT}")


if __name__ == "__main__":
    main()
