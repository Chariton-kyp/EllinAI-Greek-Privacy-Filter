from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.privacy_filter_ft.label_space import (  # noqa: E402
    assert_datasets_match_label_space,
    dataset_labels,
    load_label_space,
)


def _resolve(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that OPF JSONL labels are covered by a label-space file."
    )
    parser.add_argument(
        "--label-space",
        default="configs/label_space.json",
        help="Label-space JSON path.",
    )
    parser.add_argument("--inputs", nargs="+", required=True, help="Dataset JSONL files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    label_space_path = _resolve(args.label_space)
    input_paths = [_resolve(path) for path in args.inputs]

    labels = load_label_space(label_space_path)
    print(f"Label space: {label_space_path}")
    print(f"Classes: {len(labels) - 1} (+ O)")
    for input_path in input_paths:
        observed = sorted(dataset_labels(input_path))
        print(f"{input_path}: {len(observed)} labels")
        if observed:
            print("  " + ", ".join(observed))

    assert_datasets_match_label_space(input_paths, label_space_path)
    print("OK: every dataset label is covered by the selected label space.")


if __name__ == "__main__":
    main()
