from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


_AFM_PREFIXES = ("Α.Φ.Μ.:", "Α.Φ.Μ.", "ΑΦΜ", "Α Φ Μ", "A.F.M.:", "AFM", "EL")
_AMKA_PREFIXES = ("Α.Μ.Κ.Α.:", "Α.Μ.Κ.Α.", "ΑΜΚΑ", "AMKA")


def _strip_known_prefix(s: str, prefixes: tuple[str, ...]) -> str:
    stripped = s.strip()
    for p in prefixes:
        if stripped.startswith(p):
            return stripped[len(p):].strip(" :- \t")
    return stripped


def _normalize_digits(s: str) -> str:
    return re.sub(r"[\s\-.]", "", s)


EXPECTED_LABELS = {
    "private_person",
    "private_address",
    "private_phone",
    "private_email",
    "private_url",
    "private_date",
    "account_number",
    "secret",
    "afm",
    "amka",
    "adt",
    "iban_gr",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Greek PII OPF dataset and print label distribution."
    )
    parser.add_argument("--input", required=True, help="Input OPF JSONL path.")
    return parser.parse_args()


def _resolve(path_value: str, project_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def validate(path: Path) -> tuple[list[str], Counter, int, int, int]:
    label_counts: Counter = Counter()
    total_lines = 0
    total_spans = 0
    empty_examples = 0
    issues: list[str] = []

    with path.open("r", encoding="utf-8") as infile:
        for line_no, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue
            total_lines += 1
            payload = json.loads(line)
            text = payload.get("text", "")
            labels = payload.get("label", [])

            if not isinstance(text, str):
                issues.append(f"Line {line_no}: text must be string")
                continue
            if not isinstance(labels, list):
                issues.append(f"Line {line_no}: label must be list")
                continue

            if not labels:
                empty_examples += 1

            for idx, item in enumerate(labels):
                total_spans += 1
                if not isinstance(item, dict):
                    issues.append(f"Line {line_no}: label[{idx}] is not an object")
                    continue

                category = item.get("category")
                start = item.get("start")
                end = item.get("end")
                if not isinstance(category, str):
                    issues.append(f"Line {line_no}: label[{idx}] category must be string")
                    continue
                if category not in EXPECTED_LABELS:
                    issues.append(f"Line {line_no}: unknown label '{category}'")
                if not isinstance(start, int) or not isinstance(end, int):
                    issues.append(f"Line {line_no}: label[{idx}] start/end must be integers")
                    continue
                if start < 0 or end > len(text) or start >= end:
                    issues.append(
                        f"Line {line_no}: invalid offsets [{start},{end}] for text len {len(text)}"
                    )
                    continue

                span_str = text[start:end]
                if category == "afm":
                    digits = _normalize_digits(
                        _strip_known_prefix(span_str, _AFM_PREFIXES)
                    )
                    if not (digits.isdigit() and len(digits) == 9):
                        issues.append(
                            f"Line {line_no}: AFM malformed '{span_str}'"
                        )
                elif category == "amka":
                    digits = _normalize_digits(
                        _strip_known_prefix(span_str, _AMKA_PREFIXES)
                    )
                    if not (digits.isdigit() and len(digits) == 11):
                        issues.append(
                            f"Line {line_no}: AMKA malformed '{span_str}'"
                        )
                elif category == "iban_gr":
                    cleaned = re.sub(r"[\s\-]", "", span_str).upper()
                    if not (cleaned.startswith("GR") and len(cleaned) == 27):
                        issues.append(f"Line {line_no}: IBAN malformed '{span_str}'")

                label_counts[category] += 1

    return issues, label_counts, total_lines, total_spans, empty_examples


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    input_path = _resolve(args.input, project_root)
    issues, label_counts, total_lines, total_spans, empty_examples = validate(input_path)

    print(f"Total examples: {total_lines}")
    print(f"Total spans: {total_spans}")
    print(f"Empty (hard negatives): {empty_examples}")
    print("Label distribution:")
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"- {label}: {count}")

    if issues:
        print(f"Issues found: {len(issues)}")
        for issue in issues[:30]:
            print(f"- {issue}")
        if len(issues) > 30:
            print(f"- ... and {len(issues) - 30} more")
    else:
        print("No issues found.")


if __name__ == "__main__":
    main()
