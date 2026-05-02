from __future__ import annotations

import json
from pathlib import Path


def load_label_space(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels = payload.get("span_class_names")
    if not isinstance(labels, list) or not labels:
        raise ValueError(f"{path} must contain non-empty span_class_names list")
    if any(not isinstance(label, str) or not label for label in labels):
        raise ValueError(f"{path} contains a non-string or empty label")
    if labels[0] != "O":
        raise ValueError(f"{path} must keep 'O' as the first span class")
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise ValueError(f"{path} has duplicate labels: {duplicates}")
    return labels


def dataset_labels(path: Path) -> set[str]:
    labels: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            record_labels = payload.get("label", [])
            record_spans = payload.get("spans")
            if record_labels is None:
                record_labels = []
            if not isinstance(record_labels, list):
                raise ValueError(f"{path}:{line_number}: label must be a list")
            for index, item in enumerate(record_labels):
                if not isinstance(item, dict):
                    raise ValueError(f"{path}:{line_number}: label[{index}] must be an object")
                category = item.get("category")
                if not isinstance(category, str) or not category:
                    raise ValueError(
                        f"{path}:{line_number}: label[{index}].category must be a string"
                    )
                labels.add(category)
            if isinstance(record_spans, dict):
                for category in record_spans:
                    if not isinstance(category, str) or not category:
                        raise ValueError(f"{path}:{line_number}: spans key must be a string")
                    labels.add(category)
            elif isinstance(record_spans, list):
                for index, item in enumerate(record_spans):
                    if not isinstance(item, dict):
                        raise ValueError(
                            f"{path}:{line_number}: spans[{index}] must be an object"
                        )
                    category = item.get("label") or item.get("category")
                    if not isinstance(category, str) or not category:
                        raise ValueError(
                            f"{path}:{line_number}: spans[{index}] must include label"
                        )
                    labels.add(category)
            elif record_spans is not None:
                raise ValueError(f"{path}:{line_number}: spans must be a list or object")
    return labels


def assert_datasets_match_label_space(
    dataset_paths: list[Path],
    label_space_path: Path,
) -> None:
    span_classes = set(load_label_space(label_space_path))
    allowed = span_classes - {"O"}
    missing_by_file: dict[str, list[str]] = {}
    for dataset_path in dataset_paths:
        observed = dataset_labels(dataset_path)
        missing = sorted(observed - allowed)
        if missing:
            missing_by_file[str(dataset_path)] = missing
    if missing_by_file:
        details = "; ".join(
            f"{path}: {', '.join(labels)}" for path, labels in missing_by_file.items()
        )
        raise ValueError(
            "Dataset labels are missing from the selected label space. "
            f"Use the v2 label space for v2 datasets. Missing labels: {details}"
        )
