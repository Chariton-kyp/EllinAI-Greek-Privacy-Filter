"""Filter Qwen-generated v2.13 packs: drop records where Qwen regurgitated
internal label IDs (mac_address, ip_address, vehicle_vin, private_email,
private_person, etc.) or English-noun versions of them ('secret') as natural
Greek text. These tokens never appear in real Greek prose; training on them
teaches the model fake markers and inflates training F1 vs OOD F1.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Bare label IDs — never appear in real Greek prose
LABEL_IDS = re.compile(
    r"\b(mac_address|ip_address|vehicle_vin|account_number|private_phone|"
    r"private_email|private_person|private_address|private_url|private_date|"
    r"driver_license|license_plate|card_pan|amka|afm|adt|gemi|ama|imei|cvv|"
    r"pcn|passport)\b"
)
# "secret" as standalone English noun in Greek text — fake marker
ENGLISH_SECRET = re.compile(r"\bsecret\b", re.IGNORECASE)


def is_leaky(text: str) -> bool:
    return bool(LABEL_IDS.search(text) or ENGLISH_SECRET.search(text))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--inputs", nargs="+", type=Path, required=True)
    p.add_argument("--output-suffix", default="_clean")
    args = p.parse_args()

    for src in args.inputs:
        if not src.exists():
            print(f"SKIP missing: {src}")
            continue
        dst = src.with_name(src.stem + args.output_suffix + src.suffix)
        kept = 0
        dropped = 0
        with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
            for line in fin:
                rec = json.loads(line)
                if is_leaky(rec["text"]):
                    dropped += 1
                    continue
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                kept += 1
        print(f"{src.name}: kept={kept} dropped={dropped} -> {dst}")


if __name__ == "__main__":
    main()
