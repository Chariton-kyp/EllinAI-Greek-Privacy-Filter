"""Filter v2.X base splits: drop account_number records whose value matches
the Greek phone-format space (10 digits starting with 69, or 21..28 — mobile
or landline prefixes). These records confuse the model into labelling real
mobile phones as account_number on OOD prose.

Usage:
    python scripts/filter_phone_account_conflicts.py \\
        --input-dir  data/processed/v2_6_base_for_v2_7 \\
        --output-dir data/processed/v2_6_base_filtered
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Phone-shape: starts with 69 (mobile) OR 21-28 (landline area codes)
PHONE_LIKE_RE = re.compile(r"^(69|2[1-8])\d{8}$")


def filter_record(rec: dict) -> dict | None:
    """Return the record with phone-shaped account_number labels removed.

    If removing those labels leaves the record with zero labels AND the text
    still contains the phone-shaped digits as a free-floating token, drop the
    whole record (no useful supervision left, but the leftover digits could
    still mislead). Otherwise keep the record with the bad labels stripped.
    """
    new_labels = []
    dropped_any = False
    for L in rec.get("label", []):
        if L.get("category") == "account_number":
            seg = rec["text"][L["start"]:L["end"]]
            if PHONE_LIKE_RE.match(seg):
                dropped_any = True
                continue  # drop this label
        new_labels.append(L)
    if dropped_any and not new_labels:
        # All labels were bad → drop record entirely
        return None
    rec["label"] = new_labels
    return rec


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    total = {"records_in": 0, "records_out": 0,
             "labels_dropped": 0, "records_dropped": 0}

    for split in ("train.jsonl", "validation.jsonl", "test.jsonl", "hard_test.jsonl"):
        src = args.input_dir / split
        dst = args.output_dir / split
        if not src.exists():
            print(f"SKIP missing: {src}")
            continue

        kept = 0
        in_count = 0
        labels_dropped_split = 0
        records_dropped_split = 0
        with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
            for line in fin:
                in_count += 1
                rec = json.loads(line)
                pre = len(rec.get("label", []))
                filt = filter_record(rec)
                if filt is None:
                    records_dropped_split += 1
                    continue
                post = len(filt["label"])
                labels_dropped_split += pre - post
                fout.write(json.dumps(filt, ensure_ascii=False) + "\n")
                kept += 1

        total["records_in"] += in_count
        total["records_out"] += kept
        total["labels_dropped"] += labels_dropped_split
        total["records_dropped"] += records_dropped_split
        print(f"{split:20s}  in={in_count:>7d}  out={kept:>7d}  "
              f"labels_dropped={labels_dropped_split:>4d}  "
              f"records_dropped={records_dropped_split:>4d}")

    print(f"\nTOTAL: in={total['records_in']} out={total['records_out']} "
          f"labels_dropped={total['labels_dropped']} "
          f"records_dropped={total['records_dropped']}")


if __name__ == "__main__":
    main()
