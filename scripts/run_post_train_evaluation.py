from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate finetuned checkpoint and compare against baseline."
    )
    parser.add_argument(
        "--config",
        default="configs/fine_tune_config.yaml",
        help="Path to YAML config file.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as infile:
        return yaml.safe_load(infile)


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    cfg = load_config(config_path)
    output_cfg = cfg["output"]

    baseline_path = Path(output_cfg["baseline_metrics_file"]).expanduser()
    finetuned_path = Path(output_cfg["finetuned_metrics_file"]).expanduser()
    if not baseline_path.is_absolute():
        baseline_path = PROJECT_ROOT / baseline_path
    if not finetuned_path.is_absolute():
        finetuned_path = PROJECT_ROOT / finetuned_path
    finetuned_path.parent.mkdir(parents=True, exist_ok=True)

    eval_command = [
        "python",
        str(PROJECT_ROOT / "scripts" / "run_opf_eval.py"),
        "--config",
        str(config_path),
        "--dataset",
        "test",
        "--checkpoint",
        "finetuned",
        "--metrics-out",
        "finetuned",
    ]
    subprocess.run(eval_command, check=True, cwd=PROJECT_ROOT)

    if baseline_path.is_file():
        compare_command = [
            "python",
            str(PROJECT_ROOT / "scripts" / "compare_opf_metrics.py"),
            "--baseline",
            str(baseline_path),
            "--finetuned",
            str(finetuned_path),
        ]
        subprocess.run(compare_command, check=True, cwd=PROJECT_ROOT)
    else:
        print(f"Baseline metrics file not found: {baseline_path}")
        print("Run baseline first with: python scripts\\run_baseline.py")


if __name__ == "__main__":
    main()
