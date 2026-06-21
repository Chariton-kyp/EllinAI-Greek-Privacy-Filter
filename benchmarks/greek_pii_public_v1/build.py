"""Build cases.jsonl from cases_part_*.py modules.

Validates:
  - Every span text occurs verbatim in the case text
  - Every span label is in the 24-class label space
  - Computes char offsets (first occurrence after prior cursor)
  - No duplicate IDs across batches

Outputs:
  - cases.jsonl with {id, register, text, spans:[{label,start,end,text}]}
  - class coverage report to stdout
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "cases.jsonl"

V3_CLASSES = {
    "account_number", "adt", "afm", "ama", "amka", "card_pan", "cvv",
    "driver_license", "gemi", "iban_gr", "imei", "ip_address",
    "license_plate", "mac_address", "passport", "pcn",
    "private_address", "private_date", "private_email", "private_person",
    "private_phone", "private_url", "secret", "vehicle_vin",
}


def load_parts() -> list[dict]:
    cases: list[dict] = []
    files = sorted(ROOT.glob("cases_part_*.py"))
    if not files:
        sys.exit(f"FAIL: no cases_part_*.py at {ROOT}")
    for f in files:
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "CASES"):
            sys.exit(f"FAIL: {f.name} missing CASES list")
        cases.extend(mod.CASES)
    return cases


def resolve_offsets(case_id: int, text: str, spans: list[dict]) -> list[dict]:
    out: list[dict] = []
    cursor = 0
    for i, s in enumerate(spans):
        label = s.get("label")
        value = s.get("text")
        if label not in V3_CLASSES:
            sys.exit(f"FAIL case {case_id} span {i}: unknown label {label!r}")
        if not value:
            sys.exit(f"FAIL case {case_id} span {i}: empty span text")
        idx = text.find(value, cursor)
        if idx < 0:
            # Allow re-search from start for span repetitions (e.g. private_date appearing twice).
            idx = text.find(value)
            if idx < 0:
                sys.exit(
                    f"FAIL case {case_id} span {i}: text {value!r} not found in case"
                )
        out.append({"label": label, "start": idx, "end": idx + len(value), "text": value})
        cursor = idx + len(value)
    return out


def main() -> None:
    cases = load_parts()
    seen_ids: set[int] = set()
    written = 0
    class_counter: Counter[str] = Counter()
    register_counter: Counter[str] = Counter()

    with OUT_PATH.open("w", encoding="utf-8") as fout:
        for case in cases:
            cid = case["id"]
            if cid in seen_ids:
                sys.exit(f"FAIL: duplicate case id {cid}")
            seen_ids.add(cid)
            text = case["text"]
            spans = resolve_offsets(cid, text, case["spans"])
            for s in spans:
                class_counter[s["label"]] += 1
            register_counter[case["register"]] += 1
            rec = {
                "id": cid,
                "register": case["register"],
                "text": text,
                "spans": spans,
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"wrote {written} cases to {OUT_PATH}")
    print(f"\n=== Class coverage ({len(class_counter)} / {len(V3_CLASSES)} classes) ===")
    for cls in sorted(V3_CLASSES):
        n = class_counter.get(cls, 0)
        flag = "OK" if n >= 4 else ("LOW" if n >= 1 else "MISSING")
        print(f"  {cls:<20s} {n:>4d}  [{flag}]")
    missing = V3_CLASSES - set(class_counter)
    if missing:
        print(f"\nMISSING CLASSES: {sorted(missing)}")
    print(f"\n=== Register distribution ({len(register_counter)} unique) ===")
    for reg, n in register_counter.most_common():
        print(f"  {reg:<35s} {n}")
    print(f"\nTotal spans: {sum(class_counter.values())}")


if __name__ == "__main__":
    main()
