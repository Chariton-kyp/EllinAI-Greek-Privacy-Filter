from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.privacy_filter_ft.schema import PrivacyExample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate privacy-filter JSONL dataset.")
    parser.add_argument("--input", required=True, help="Input JSONL file path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    valid_rows = 0
    with input_path.open("r", encoding="utf-8") as infile:
        for line_number, line in enumerate(infile, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            try:
                PrivacyExample.from_dict(payload)
            except ValueError as exc:
                raise ValueError(f"Validation error on line {line_number}: {exc}") from exc
            valid_rows += 1

    if valid_rows == 0:
        raise ValueError("Dataset is empty after filtering blank lines.")

    print(f"Validation successful. Rows: {valid_rows}")


if __name__ == "__main__":
    main()
