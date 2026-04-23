from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run baseline evaluation on test split with base OPF checkpoint."
    )
    parser.add_argument(
        "--config",
        default="configs/fine_tune_config.yaml",
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--eval-mode",
        choices=("typed", "untyped"),
        default=None,
        help="Override eval mode for baseline run.",
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
    metrics_path = Path(output_cfg["baseline_metrics_file"]).expanduser()
    if not metrics_path.is_absolute():
        metrics_path = PROJECT_ROOT / metrics_path
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "python",
        str(PROJECT_ROOT / "scripts" / "run_opf_eval.py"),
        "--config",
        str(config_path),
        "--dataset",
        "test",
        "--checkpoint",
        "base",
        "--metrics-out",
        "baseline",
    ]
    if args.eval_mode is not None:
        command.extend(["--eval-mode", args.eval_mode])
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)
    print(f"Baseline metrics saved to: {metrics_path}")


if __name__ == "__main__":
    main()
