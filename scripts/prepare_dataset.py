from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.privacy_filter_ft.schema import PrivacyExample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert CSV/JSONL dataset to OPF-compatible JSONL format."
    )
    parser.add_argument("--input", required=True, help="Input CSV or JSONL file path.")
    parser.add_argument("--output", required=True, help="Output JSONL file path.")
    parser.add_argument("--text-column", default="text", help="Text column/key name.")
    parser.add_argument(
        "--example-id-column",
        default="example_id",
        help="Grouping key column for multiple spans per record.",
    )
    parser.add_argument(
        "--category-column",
        default="category",
        help="Span category column (e.g. private_person).",
    )
    parser.add_argument("--start-column", default="start", help="Span start offset column.")
    parser.add_argument("--end-column", default="end", help="Span end offset column.")
    parser.add_argument(
        "--info-columns",
        nargs="*",
        default=[],
        help="Optional columns copied into OPF 'info' object.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path).to_dict(orient="records")
    if suffix == ".jsonl":
        rows: list[dict] = []
        with path.open("r", encoding="utf-8") as infile:
            for line in infile:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    raise ValueError("Unsupported input format. Use CSV or JSONL.")


def _coerce_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Field '{field_name}' must be an integer offset.")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    raise ValueError(f"Field '{field_name}' must be an integer offset.")


def _build_record_from_row(args: argparse.Namespace, row: dict) -> dict:
    text = row.get(args.text_column)
    category = row.get(args.category_column)
    start = _coerce_int(row.get(args.start_column), args.start_column)
    end = _coerce_int(row.get(args.end_column), args.end_column)

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Missing/invalid text in column '{args.text_column}'.")
    if not isinstance(category, str) or not category.strip():
        raise ValueError(f"Missing/invalid category in column '{args.category_column}'.")
    if not (0 <= start < end <= len(text)):
        raise ValueError(
            f"Invalid offsets [{start}, {end}] for text length {len(text)}."
        )

    span_text = text[start:end]
    span_label = category.strip()
    span_key = f"{span_label}: {span_text}" if span_text else span_label
    record: dict[str, object] = {
        "text": text,
        "spans": {span_key: [[start, end]]},
    }

    info = {key: row.get(key) for key in args.info_columns if key in row}
    if info:
        record["info"] = info
    return record


def _merge_csv_rows(args: argparse.Namespace, rows: list[dict]) -> list[dict]:
    grouped: dict[object, dict[str, object]] = {}
    order: list[object] = []

    for index, row in enumerate(rows):
        record = _build_record_from_row(args, row)
        group_key = (
            row[args.example_id_column]
            if args.example_id_column in row
            else f"__row_{index}"
        )

        if group_key not in grouped:
            grouped[group_key] = {
                "text": record["text"],
                "spans": defaultdict(list),
                "info": {},
            }
            order.append(group_key)

        current = grouped[group_key]
        if current["text"] != record["text"]:
            raise ValueError(
                f"Rows with same '{args.example_id_column}' must have identical text."
            )

        for key, offsets in record["spans"].items():
            current["spans"][key].extend(offsets)
        for key, value in record.get("info", {}).items():
            if key not in current["info"]:
                current["info"][key] = value

    merged: list[dict] = []
    for key in order:
        item = grouped[key]
        payload: dict[str, object] = {
            "text": item["text"],
            "spans": dict(item["spans"]),
        }
        if item["info"]:
            payload["info"] = item["info"]
        merged.append(payload)
    return merged


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser()
    output_path = Path(args.output).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    rows = load_rows(input_path)
    prepared_rows = rows if input_path.suffix.lower() == ".jsonl" else _merge_csv_rows(args, rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as outfile:
        for row in prepared_rows:
            example = PrivacyExample.from_dict(row)
            outfile.write(json.dumps(example.to_dict(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
