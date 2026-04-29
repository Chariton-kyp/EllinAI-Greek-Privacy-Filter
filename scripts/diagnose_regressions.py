"""Compare v2 vs v2.5 benchmark triage. Show cases where v2 was right and
v2.5 went wrong, especially for regressed classes (private_phone,
license_plate, ama). Print what v2.5 predicted instead.

Usage:
    python scripts/diagnose_regressions.py
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
V2 = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_triage.json"
V25 = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_triage_v2_5.json"


def overlap(a, b) -> bool:
    return max(a["start"], b["start"]) < min(a["end"], b["end"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--v2", type=Path, default=V2)
    ap.add_argument("--v2-5", type=Path, default=V25)
    ap.add_argument("--classes", nargs="*", default=["private_phone", "license_plate", "ama"])
    ap.add_argument("--max-cases", type=int, default=20)
    args = ap.parse_args()

    v2 = json.loads(args.v2.read_text(encoding="utf-8"))
    v25 = json.loads(args.v2_5.read_text(encoding="utf-8"))

    v2_cases = {c["case_id"]: c for c in v2["results"]["viterbi"]["per_case"]}
    v25_cases = {c["case_id"]: c for c in v25["results"]["viterbi"]["per_case"]}

    for cls in args.classes:
        print(f"\n========== {cls} ==========")
        v2_recall_count = 0
        v2_5_recall_count = 0
        regressed = []  # cases v2 caught but v2.5 missed/mis-classified
        for cid, v2_case in v2_cases.items():
            v25_case = v25_cases[cid]
            for exp in v2_case["expected"]:
                if exp["label"] != cls:
                    continue
                # v2 prediction state
                v2_match = any(
                    p for p in v2_case["predicted"]
                    if p["label"] == cls and overlap(p, exp)
                )
                v25_match = any(
                    p for p in v25_case["predicted"]
                    if p["label"] == cls and overlap(p, exp)
                )
                if v2_match:
                    v2_recall_count += 1
                if v25_match:
                    v2_5_recall_count += 1
                if v2_match and not v25_match:
                    # find what v2.5 predicted on the overlapping span
                    alt = next(
                        (p for p in v25_case["predicted"]
                         if overlap(p, exp)),
                        None
                    )
                    regressed.append({
                        "case_id": cid,
                        "register": v2_case["register"],
                        "expected_text": exp["text"],
                        "v2_5_predicted_label": alt["label"] if alt else "<NOTHING>",
                        "v2_5_predicted_text": alt["text"] if alt else "",
                        "context": v2_case["text"][max(0, exp["start"]-30):exp["end"]+30],
                    })

        print(f"v2 recall: {v2_recall_count}")
        print(f"v2.5 recall: {v2_5_recall_count}")
        print(f"regressed cases: {len(regressed)}")
        if regressed:
            alt_label_dist = Counter(r["v2_5_predicted_label"] for r in regressed)
            print(f"v2.5 alt label distribution: {dict(alt_label_dist)}")
            print()
            for r in regressed[:args.max_cases]:
                print(f"  case {r['case_id']} ({r['register']}):")
                print(f"    expected: [{cls}] '{r['expected_text']}'")
                print(f"    v2.5 said: [{r['v2_5_predicted_label']}] '{r['v2_5_predicted_text']}'")
                print(f"    context: ...{r['context']}...")
                print()


if __name__ == "__main__":
    main()
