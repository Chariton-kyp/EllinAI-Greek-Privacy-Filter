"""Rewrite email and URL spans whose content contains Greek characters
into their Latin transliteration, keeping offsets consistent.

Rationale: real-world Greek emails and URLs overwhelmingly use Latin
transliterations of names (giorgos.papadopoulos@gmail.com) rather than
Greek-script IDNs. Rule-based generators may have produced Greek-script
email local-parts and URL slugs; this tool normalizes them.

A small fraction (`--keep-greek-ratio`, default 0.2) is left untouched
so the trained model still sees both scripts.

Usage:

    python scripts/postprocess_latinize_contacts.py \
        --input data/processed/greek_v2_raw.jsonl \
        --output data/processed/greek_v2_fixed.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from privacy_filter_ft.transliteration import transliterate_greek  # noqa: E402


TARGET_CATEGORIES = {"private_email", "private_url"}
_GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def fix_record(record: dict, rng: random.Random, keep_greek_ratio: float) -> dict:
    text = record.get("text", "")
    spans = sorted(record.get("label") or [], key=lambda sp: sp["start"])
    if not spans:
        return record
    new_text_parts: list[str] = []
    new_spans: list[dict] = []
    cursor = 0
    for sp in spans:
        new_text_parts.append(text[cursor:sp["start"]])
        old_val = text[sp["start"]:sp["end"]]
        if (
            sp["category"] in TARGET_CATEGORIES
            and _GREEK_RE.search(old_val)
            and rng.random() >= keep_greek_ratio
        ):
            new_val = transliterate_greek(old_val)
        else:
            new_val = old_val
        new_start = sum(len(p) for p in new_text_parts)
        new_text_parts.append(new_val)
        new_end = sum(len(p) for p in new_text_parts)
        new_spans.append(
            {"category": sp["category"], "start": new_start, "end": new_end}
        )
        cursor = sp["end"]
    new_text_parts.append(text[cursor:])
    return {
        "text": "".join(new_text_parts),
        "label": new_spans,
        "info": record.get("info", {}),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument(
        "--keep-greek-ratio", type=float, default=0.2,
        help="Fraction of Greek-script contact values to leave untouched "
             "(for script diversity). 0.0 = latinize all.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    inp = Path(args.input)
    if not inp.is_absolute():
        inp = PROJECT_ROOT / inp
    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    n_fixed = 0
    with inp.open("r", encoding="utf-8") as ifp, out.open("w", encoding="utf-8") as ofp:
        for line in ifp:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            n += 1
            new_record = fix_record(record, rng, args.keep_greek_ratio)
            if new_record["text"] != record["text"]:
                n_fixed += 1
            ofp.write(json.dumps(new_record, ensure_ascii=False) + "\n")
    print(f"Processed {n} records, rewrote {n_fixed} with Latin email/URL")


if __name__ == "__main__":
    main()
