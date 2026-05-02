from __future__ import annotations

from pathlib import Path
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.privacy_filter_ft.label_space import assert_datasets_match_label_space


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as infile:
        return yaml.safe_load(infile)


def mark(status: bool) -> str:
    return "OK" if status else "MISSING"


def main() -> None:
    cfg_path = PROJECT_ROOT / "configs" / "fine_tune_config.yaml"
    cfg = load_config(cfg_path)

    opf_cfg = cfg["opf"]
    data_cfg = cfg["data"]
    output_cfg = cfg["output"]
    label_space_cfg = cfg.get("label_space") or {}

    upstream_dir = Path(opf_cfg["upstream_local_dir"]).expanduser()
    checkpoint_dir = Path(opf_cfg["checkpoint_local_dir"]).expanduser()
    train_file = Path(data_cfg["train_file"]).expanduser()
    validation_file = Path(data_cfg["validation_file"]).expanduser()
    test_file = Path(data_cfg["test_file"]).expanduser()
    label_space_file = Path(
        label_space_cfg.get("path", "configs/label_space.json")
    ).expanduser()
    baseline_metrics = Path(output_cfg["baseline_metrics_file"]).expanduser()
    finetuned_metrics = Path(output_cfg["finetuned_metrics_file"]).expanduser()

    path_values = [
        upstream_dir,
        checkpoint_dir,
        train_file,
        validation_file,
        test_file,
        label_space_file,
        baseline_metrics,
        finetuned_metrics,
    ]
    for i, path in enumerate(path_values):
        if not path.is_absolute():
            path_values[i] = PROJECT_ROOT / path
    (
        upstream_dir,
        checkpoint_dir,
        train_file,
        validation_file,
        test_file,
        label_space_file,
        baseline_metrics,
        finetuned_metrics,
    ) = path_values

    label_space_ok = False
    label_space_error = ""
    if label_space_file.is_file() and train_file.is_file() and validation_file.is_file():
        try:
            assert_datasets_match_label_space(
                [train_file, validation_file],
                label_space_file,
            )
            label_space_ok = True
        except ValueError as exc:
            label_space_error = str(exc)

    prerequisite_checks = {
        "Config file": cfg_path.is_file(),
        "Upstream repo dir": upstream_dir.is_dir(),
        "Base checkpoint dir": checkpoint_dir.is_dir(),
        "Base checkpoint config.json": (checkpoint_dir / "config.json").is_file(),
        "Base checkpoint model.safetensors": (checkpoint_dir / "model.safetensors").is_file(),
        "Train dataset": train_file.is_file(),
        "Validation dataset": validation_file.is_file(),
        "Test dataset": test_file.is_file(),
        "Label space file": label_space_file.is_file(),
        "Train/validation labels covered by label space": label_space_ok,
    }
    artifact_checks = {
        "Baseline metrics file": baseline_metrics.is_file(),
        "Finetuned metrics file": finetuned_metrics.is_file(),
    }

    print("Readiness report (prerequisites):")
    for name, status in prerequisite_checks.items():
        print(f"- {name}: {mark(status)}")
    if label_space_error:
        print(f"  label-space error: {label_space_error}")

    print("Readiness report (produced artifacts):")
    for name, status in artifact_checks.items():
        print(f"- {name}: {mark(status)}")

    if not all(prerequisite_checks.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
