from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split one JSONL dataset into train/validation/test files."
    )
    parser.add_argument("--input", required=True, help="Input JSONL path.")
    parser.add_argument("--train-out", required=True, help="Output train JSONL path.")
    parser.add_argument("--validation-out", required=True, help="Output validation JSONL path.")
    parser.add_argument("--test-out", required=True, help="Output test JSONL path.")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--validation-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=1337)
    return parser.parse_args()


def _resolve(path_value: str, project_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as outfile:
        for row in rows:
            outfile.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    ratio_sum = args.train_ratio + args.validation_ratio + args.test_ratio
    if abs(ratio_sum - 1.0) > 1e-9:
        raise ValueError("train/validation/test ratios must sum to 1.0")

    project_root = Path(__file__).resolve().parents[1]
    input_path = _resolve(args.input, project_root)
    train_out = _resolve(args.train_out, project_root)
    validation_out = _resolve(args.validation_out, project_root)
    test_out = _resolve(args.test_out, project_root)

    rows: list[dict] = []
    with input_path.open("r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    rng = random.Random(args.seed)
    rng.shuffle(rows)

    total = len(rows)
    train_end = int(total * args.train_ratio)
    validation_end = train_end + int(total * args.validation_ratio)
    train_rows = rows[:train_end]
    validation_rows = rows[train_end:validation_end]
    test_rows = rows[validation_end:]

    _write_jsonl(train_out, train_rows)
    _write_jsonl(validation_out, validation_rows)
    _write_jsonl(test_out, test_rows)

    print(f"Total: {total}")
    print(f"Train: {len(train_rows)} -> {train_out}")
    print(f"Validation: {len(validation_rows)} -> {validation_out}")
    print(f"Test: {len(test_rows)} -> {test_out}")


if __name__ == "__main__":
    main()
