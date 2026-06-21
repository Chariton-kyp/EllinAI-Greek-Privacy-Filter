"""Regenerate duplicate PII values across cases_part_*.py with unique alternatives.

Reads:  cases.jsonl (built artifact with current duplicates)
Identifies duplicate values per class (AFM, AMKA, IBAN, passport, VIN,
plate, driver_license, GEMI, account_number).
Generates unique format-correct replacements.
Emits replacement mapping → applied via search-and-replace to source files.

Strategy:
  - Each duplicate value gets reduced to ≤2 occurrences globally.
  - First 2 occurrences keep original (with unique-personal context
    if same person across cases means deliberate consistency).
  - 3rd+ occurrence replaced with new format-correct value.

Run:
  python benchmarks/greek_pii_public_v1/_regenerate_seeds.py
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES_JSONL = ROOT / "cases.jsonl"
PARTS = sorted(ROOT.glob("cases_part_*.py"))

rng = random.Random(20260509)

# Format-correct generators (no validation of real Greek registry data;
# values are synthetic but follow on-the-wire format conventions).

def gen_afm() -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(9))


def gen_amka(year: int = 1985, month: int = 5, day: int = 15) -> str:
    """11-digit, first 6 = DDMMYY of birthdate (random plausible)."""
    yr = rng.randint(1955, 2010)
    mo = rng.randint(1, 12)
    dy = rng.randint(1, 28)
    suffix = "".join(str(rng.randint(0, 9)) for _ in range(5))
    return f"{dy:02d}{mo:02d}{yr % 100:02d}{suffix}"


def gen_adt() -> str:
    """Greek ID: 2 Greek letters + 6 digits."""
    letters = "ΑΒΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    pre = "".join(rng.choice(letters) for _ in range(2))
    suf = "".join(str(rng.randint(0, 9)) for _ in range(6))
    return f"{pre}-{suf}"


def gen_iban_gr() -> str:
    """GR + 25 alnum (formatted with spaces)."""
    body = "".join(str(rng.randint(0, 9)) for _ in range(25))
    formatted = " ".join([f"GR{body[:2]}", body[2:6], body[6:10], body[10:14], body[14:18], body[18:22], body[22:25]])
    return formatted


def gen_passport_gr() -> str:
    """Greek passport: 2 Greek letters + 7 digits."""
    letters = "ΑΒΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    pre = "".join(rng.choice(letters) for _ in range(2))
    suf = "".join(str(rng.randint(0, 9)) for _ in range(7))
    return f"{pre}{suf}"


def gen_passport_latin() -> str:
    """EU passport (Latin): 2 Latin letters + 7 digits."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    pre = "".join(rng.choice(letters) for _ in range(2))
    suf = "".join(str(rng.randint(0, 9)) for _ in range(7))
    return f"{pre}{suf}"


def gen_vin() -> str:
    """17-char VIN, exclude I/O/Q."""
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return "".join(rng.choice(chars) for _ in range(17))


def gen_plate_gr() -> str:
    """Modern Greek civilian plate: 3 Greek letters (lookalikes) + 4 digits."""
    letters = "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"  # canonical Greek-Latin lookalike subset
    pre = "".join(rng.choice(letters) for _ in range(3))
    suf = "".join(str(rng.randint(0, 9)) for _ in range(4))
    return f"{pre}-{suf}"


def gen_driver_license() -> str:
    """9-digit driver license number."""
    return "".join(str(rng.randint(0, 9)) for _ in range(9))


def gen_gemi() -> str:
    """12-digit GEMI registry number."""
    return "".join(str(rng.randint(0, 9)) for _ in range(12))


def gen_pcn() -> str:
    """ΠΑΠ format: 9 digits + 1 uppercase letter + 2 digits."""
    pre = "".join(str(rng.randint(0, 9)) for _ in range(9))
    letter = rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    suf = "".join(str(rng.randint(0, 9)) for _ in range(2))
    return f"{pre}{letter}{suf}"


GENERATORS = {
    "afm": gen_afm,
    "amka": gen_amka,
    "adt": gen_adt,
    "iban_gr": gen_iban_gr,
    "passport": gen_passport_gr,
    "vehicle_vin": gen_vin,
    "license_plate": gen_plate_gr,
    "driver_license": gen_driver_license,
    "gemi": gen_gemi,
    "pcn": gen_pcn,
}


def main() -> None:
    # Load all cases
    cases: list[dict] = []
    with CASES_JSONL.open(encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))

    # Find duplicates per class
    value_to_cases: dict = defaultdict(list)  # (label, value) → [case_id, ...]
    for case in cases:
        for s in case["spans"]:
            value_to_cases[(s["label"], s["text"])].append(case["id"])

    # Identify values that appear in 3+ cases — must reduce to ≤2
    duplicates: list[tuple] = []
    for (label, value), cids in value_to_cases.items():
        if label in GENERATORS and len(cids) > 2:
            duplicates.append((label, value, cids))

    # Build replacement plan: for occurrences 3..N, generate unique alternative
    # PER occurrence (case-specific replacement)
    plan: dict = {}  # case_id → list of (old, new)
    used_values = {label: set() for label in GENERATORS}
    # Pre-populate with all current values to avoid collisions
    for (label, value), cids in value_to_cases.items():
        if label in GENERATORS:
            used_values[label].add(value)

    print("=== Duplicate report (>=3 occurrences) ===")
    for label, value, cids in sorted(duplicates, key=lambda x: -len(x[2])):
        print(f"  {label:<18s} {value:<40s} ×{len(cids)} cases {cids}")

    # For each duplicate (cases 3..N), generate a unique replacement
    for label, value, cids in duplicates:
        for cid in cids[2:]:  # keep first 2 occurrences, replace 3rd+
            gen = GENERATORS[label]
            # generate until unique
            for _ in range(100):
                new_value = gen()
                if new_value not in used_values[label]:
                    break
            used_values[label].add(new_value)
            plan.setdefault(cid, []).append((label, value, new_value))

    print(f"\n=== Replacement plan ({sum(len(v) for v in plan.values())} edits across {len(plan)} cases) ===")
    for cid in sorted(plan):
        for label, old, new in plan[cid]:
            print(f"  case {cid}: {label} {old} → {new}")

    # Apply edits to cases_part_*.py source files
    edits_applied = 0
    for part_path in PARTS:
        text = part_path.read_text(encoding="utf-8")
        original = text
        # Find which cases live in this part by parsing case ids
        # Heuristic: find every "id": N pattern
        case_ids_in_file = set(int(m.group(1)) for m in re.finditer(r'"id":\s*(\d+)', text))
        for cid in plan:
            if cid not in case_ids_in_file:
                continue
            for label, old, new in plan[cid]:
                # Replace ONLY occurrences within this case block. To avoid
                # cross-case collisions, find the case block by id and
                # operate within it.
                pattern = re.compile(
                    r'(\{\s*"id":\s*' + str(cid) + r'\b.*?(?=\n\s*\{\s*"id":|\Z))',
                    re.DOTALL
                )
                m = pattern.search(text)
                if not m:
                    print(f"  WARN: case {cid} not found in {part_path.name}")
                    continue
                block = m.group(1)
                if old not in block:
                    print(f"  WARN: {old!r} not found in case {cid} block")
                    continue
                new_block = block.replace(old, new)
                text = text[:m.start()] + new_block + text[m.end():]
                edits_applied += 1
        if text != original:
            part_path.write_text(text, encoding="utf-8")
            print(f"  patched {part_path.name}")

    print(f"\nApplied {edits_applied} edits.")


if __name__ == "__main__":
    main()
