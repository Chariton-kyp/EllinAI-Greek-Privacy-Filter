from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OPF fine-tuning using project YAML config."
    )
    parser.add_argument(
        "--config",
        default="configs/fine_tune_config.yaml",
        help="Path to YAML config file.",
    )
    parser.add_argument("--device", default=None, help="Override device (e.g. cuda, cpu).")
    parser.add_argument("--n-ctx", type=int, default=None, help="Override context window.")
    parser.add_argument("--epochs", type=int, default=None, help="Override epoch count.")
    parser.add_argument("--batch-size", type=int, default=None, help="Override train batch size.")
    parser.add_argument(
        "--grad-accum-steps",
        type=int,
        default=None,
        help="Override gradient accumulation steps.",
    )
    parser.add_argument(
        "--learning-rate", type=float, default=None, help="Override learning rate."
    )
    parser.add_argument(
        "--weight-decay", type=float, default=None, help="Override weight decay."
    )
    parser.add_argument(
        "--max-grad-norm", type=float, default=None, help="Override max grad norm."
    )
    parser.add_argument(
        "--output-param-dtype",
        choices=("inherit", "bf16", "fp32"),
        default=None,
        help="Override saved-weights dtype.",
    )
    parser.add_argument(
        "--max-train-examples",
        type=int,
        default=None,
        help="Optional cap on loaded training examples (useful for smoke tests).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the opf train command that would be executed and exit.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as infile:
        return yaml.safe_load(infile)


def _resolve(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> None:
    args = parse_args()
    cfg = load_config(_resolve(args.config))

    opf_cfg = cfg["opf"]
    data_cfg = cfg["data"]
    train_cfg = cfg["training"]
    output_cfg = cfg["output"]
    label_space_cfg = cfg.get("label_space") or {}

    output_dir = _resolve(output_cfg["final_model_dir"])
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    train_file = _resolve(data_cfg["train_file"])
    validation_file = _resolve(data_cfg["validation_file"])
    checkpoint_dir = _resolve(opf_cfg["checkpoint_local_dir"])

    if not train_file.is_file():
        raise FileNotFoundError(f"Train dataset not found: {train_file}")
    if not validation_file.is_file():
        raise FileNotFoundError(f"Validation dataset not found: {validation_file}")
    if not checkpoint_dir.is_dir():
        raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")

    device = args.device or opf_cfg["device"]
    n_ctx = args.n_ctx if args.n_ctx is not None else opf_cfg["n_ctx"]
    epochs = args.epochs if args.epochs is not None else train_cfg["epochs"]
    batch_size = args.batch_size if args.batch_size is not None else train_cfg["batch_size"]
    grad_accum_steps = (
        args.grad_accum_steps
        if args.grad_accum_steps is not None
        else train_cfg["grad_accum_steps"]
    )
    learning_rate = (
        args.learning_rate if args.learning_rate is not None else train_cfg["learning_rate"]
    )
    weight_decay = (
        args.weight_decay if args.weight_decay is not None else train_cfg["weight_decay"]
    )
    max_grad_norm = (
        args.max_grad_norm if args.max_grad_norm is not None else train_cfg["max_grad_norm"]
    )
    output_param_dtype = (
        args.output_param_dtype
        if args.output_param_dtype is not None
        else train_cfg.get("output_param_dtype", "inherit")
    )

    command = [
        "python",
        "-m",
        "opf",
        "train",
        str(train_file),
        "--validation-dataset",
        str(validation_file),
        "--checkpoint",
        str(checkpoint_dir),
        "--output-dir",
        str(output_dir),
        "--device",
        device,
        "--n-ctx",
        str(n_ctx),
        "--epochs",
        str(epochs),
        "--batch-size",
        str(batch_size),
        "--grad-accum-steps",
        str(grad_accum_steps),
        "--learning-rate",
        str(learning_rate),
        "--weight-decay",
        str(weight_decay),
        "--max-grad-norm",
        str(max_grad_norm),
        "--shuffle-seed",
        str(train_cfg["seed"]),
        "--output-param-dtype",
        output_param_dtype,
    ]

    if train_cfg.get("overwrite_output", False):
        command.append("--overwrite-output")

    if args.max_train_examples is not None:
        command.extend(["--max-train-examples", str(args.max_train_examples)])

    # Label space resolution order:
    #   1. configs/fine_tune_config.yaml -> label_space.path
    #   2. fallback: configs/label_space.json (legacy behaviour)
    label_space_path = None
    if label_space_cfg.get("path"):
        candidate = _resolve(label_space_cfg["path"])
        if candidate.is_file():
            label_space_path = candidate
        else:
            raise FileNotFoundError(
                f"label_space.path in config does not exist: {candidate}"
            )
    else:
        legacy = PROJECT_ROOT / "configs" / "label_space.json"
        if legacy.is_file():
            label_space_path = legacy

    if label_space_path is not None:
        command.extend(["--label-space-json", str(label_space_path)])
        print(f"[run_opf_train] Using custom label space: {label_space_path}")
    else:
        print(
            "[run_opf_train] WARNING: no label space JSON resolved. "
            "Custom categories (amka/afm/adt/iban_gr) will be ignored."
        )

    # Ensure a place to stream the training log even if the caller doesn't tee.
    train_log = output_cfg.get("train_log")
    if train_log:
        log_path = _resolve(train_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[run_opf_train] Train log target: {log_path}")

    print("[run_opf_train] Command:")
    print("  " + " ".join(command))

    if args.dry_run:
        return

    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    main()
