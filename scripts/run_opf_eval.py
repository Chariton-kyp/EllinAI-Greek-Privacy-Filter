from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OPF evaluation using project YAML config."
    )
    parser.add_argument(
        "--config",
        default="configs/fine_tune_config.yaml",
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--dataset",
        choices=("train", "validation", "test"),
        default="test",
        help="Dataset split to evaluate.",
    )
    parser.add_argument(
        "--checkpoint",
        choices=("base", "finetuned"),
        default="base",
        help="Which checkpoint to evaluate.",
    )
    parser.add_argument(
        "--eval-mode",
        choices=("typed", "untyped"),
        default=None,
        help="Override eval mode from config.",
    )
    parser.add_argument(
        "--metrics-out",
        choices=("none", "baseline", "finetuned"),
        default="baseline",
        help="Write metrics file path from config, or disable output with 'none'.",
    )
    parser.add_argument("--device", default=None, help="Override device (e.g. cuda, cpu).")
    parser.add_argument("--n-ctx", type=int, default=None, help="Override context window.")
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

    opf_cfg = cfg["opf"]
    data_cfg = cfg["data"]
    output_cfg = cfg["output"]
    eval_cfg = cfg.get("evaluation", {})

    dataset_map = {
        "train": data_cfg["train_file"],
        "validation": data_cfg["validation_file"],
        "test": data_cfg["test_file"],
    }
    dataset = dataset_map[args.dataset]
    checkpoint = (
        opf_cfg["checkpoint_local_dir"]
        if args.checkpoint == "base"
        else output_cfg["final_model_dir"]
    )
    dataset_path = Path(dataset).expanduser()
    checkpoint_path = Path(checkpoint).expanduser()
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path
    if not checkpoint_path.is_absolute():
        checkpoint_path = PROJECT_ROOT / checkpoint_path
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    if not checkpoint_path.is_dir():
        raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_path}")
    eval_mode = args.eval_mode or eval_cfg.get("eval_mode", "typed")
    device = args.device or opf_cfg["device"]
    n_ctx = args.n_ctx if args.n_ctx is not None else opf_cfg["n_ctx"]

    metrics_file = None
    if args.metrics_out == "baseline":
        metrics_file = output_cfg["baseline_metrics_file"]
    elif args.metrics_out == "finetuned":
        metrics_file = output_cfg["finetuned_metrics_file"]

    command = [
        "python",
        "-m",
        "opf",
        "eval",
        str(dataset_path),
        "--checkpoint",
        str(checkpoint_path),
        "--device",
        device,
        "--n-ctx",
        str(n_ctx),
        "--eval-mode",
        eval_mode,
    ]
    if metrics_file is not None:
        metrics_path = Path(metrics_file).expanduser()
        if not metrics_path.is_absolute():
            metrics_path = PROJECT_ROOT / metrics_path
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        command.extend(["--metrics-out", str(metrics_path)])
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    main()
