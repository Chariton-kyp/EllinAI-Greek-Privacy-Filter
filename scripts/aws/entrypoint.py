"""SageMaker container-side entrypoint for Greek Privacy Filter fine-tuning.

SageMaker invokes this script inside the training container with the
following conventions:

  /opt/ml/input/data/train/        <- train.jsonl (from S3 channel 'train')
  /opt/ml/input/data/validation/   <- validation.jsonl (channel 'validation')
  /opt/ml/input/data/test/         <- test.jsonl (channel 'test')
  /opt/ml/input/data/checkpoint/   <- base HF checkpoint (channel 'checkpoint')
  /opt/ml/input/data/labels/       <- label_space.json (channel 'labels')
  /opt/ml/model/                   <- writable; final checkpoint goes here
  /opt/ml/output/data/             <- extra artifacts (metrics, logs)

The upstream opf source is bundled into the image via /opt/ml/code/external/privacy-filter
by sagemaker_train.py (which uploads this repo as the source_dir).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SM_INPUT = Path(os.environ.get("SM_INPUT_DIR", "/opt/ml/input"))
SM_MODEL_DIR = Path(os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
SM_OUTPUT_DATA_DIR = Path(os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data"))
SM_CHANNELS = SM_INPUT / "data"


def _pick_file(channel: str, *suffixes: str) -> Path:
    channel_dir = SM_CHANNELS / channel
    if not channel_dir.is_dir():
        raise FileNotFoundError(f"SageMaker channel missing: {channel_dir}")
    for suffix in suffixes or ("",):
        matches = sorted(channel_dir.rglob(f"*{suffix}")) if suffix else sorted(
            channel_dir.rglob("*")
        )
        for match in matches:
            if match.is_file():
                return match
    raise FileNotFoundError(
        f"No file matching {suffixes!r} found in channel {channel_dir}"
    )


def _install_opf() -> None:
    """Install the pinned opf package that is bundled with source_dir."""
    repo_root = Path(__file__).resolve().parents[2]
    opf_src = repo_root / "external" / "privacy-filter"
    if not opf_src.is_dir():
        raise FileNotFoundError(
            f"Bundled opf source not found at {opf_src}. "
            "Make sure sagemaker_train.py uploaded it as source_dir."
        )
    print(f"[entrypoint] Installing opf from {opf_src}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(opf_src)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum-steps", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--n-ctx", type=int, default=256)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument(
        "--output-param-dtype", choices=("inherit", "bf16", "fp32"), default="bf16"
    )
    parser.add_argument(
        "--eval-mode", choices=("typed", "untyped"), default="typed"
    )
    parser.add_argument(
        "--skip-test-eval", action="store_true",
        help="Skip post-finetune evaluation (e.g. when you only have train/val).",
    )
    args = parser.parse_args()

    _install_opf()

    train_file = _pick_file("train", ".jsonl")
    validation_file = _pick_file("validation", ".jsonl")
    label_space_file = _pick_file("labels", ".json")
    checkpoint_dir = SM_CHANNELS / "checkpoint"
    if not checkpoint_dir.is_dir():
        raise FileNotFoundError(f"Checkpoint channel missing: {checkpoint_dir}")

    finetune_dir = SM_MODEL_DIR
    finetune_dir.mkdir(parents=True, exist_ok=True)
    SM_OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[entrypoint] Train:       {train_file}")
    print(f"[entrypoint] Validation:  {validation_file}")
    print(f"[entrypoint] Labels:      {label_space_file}")
    print(f"[entrypoint] Checkpoint:  {checkpoint_dir}")
    print(f"[entrypoint] Output:      {finetune_dir}")

    train_cmd = [
        sys.executable, "-m", "opf", "train", str(train_file),
        "--validation-dataset", str(validation_file),
        "--checkpoint", str(checkpoint_dir),
        "--output-dir", str(finetune_dir),
        "--label-space-json", str(label_space_file),
        "--device", "cuda",
        "--n-ctx", str(args.n_ctx),
        "--epochs", str(args.epochs),
        "--batch-size", str(args.batch_size),
        "--grad-accum-steps", str(args.grad_accum_steps),
        "--learning-rate", str(args.learning_rate),
        "--weight-decay", str(args.weight_decay),
        "--max-grad-norm", str(args.max_grad_norm),
        "--shuffle-seed", str(args.seed),
        "--output-param-dtype", args.output_param_dtype,
        "--overwrite-output",
    ]
    print("[entrypoint] train command:", " ".join(train_cmd))
    subprocess.run(train_cmd, check=True)

    # Copy the bundled label_space.json into the model artifact so the
    # finetuned checkpoint is self-describing when loaded elsewhere.
    try:
        shutil.copy2(label_space_file, finetune_dir / "label_space.json")
    except Exception as exc:  # noqa: BLE001
        print(f"[entrypoint] WARN: could not copy label_space.json: {exc}")

    # Optional post-finetune evaluation on test channel (if provided).
    test_dir = SM_CHANNELS / "test"
    if not args.skip_test_eval and test_dir.is_dir():
        try:
            test_file = _pick_file("test", ".jsonl")
        except FileNotFoundError:
            test_file = None
        if test_file is not None:
            metrics_path = SM_OUTPUT_DATA_DIR / "finetuned_test_metrics.json"
            eval_cmd = [
                sys.executable, "-m", "opf", "eval", str(test_file),
                "--checkpoint", str(finetune_dir),
                "--device", "cuda",
                "--n-ctx", str(args.n_ctx),
                "--eval-mode", args.eval_mode,
                "--metrics-out", str(metrics_path),
            ]
            print("[entrypoint] eval command:", " ".join(eval_cmd))
            subprocess.run(eval_cmd, check=True)

            try:
                print("[entrypoint] Final metrics preview:")
                print(json.dumps(
                    json.loads(metrics_path.read_text(encoding="utf-8")).get(
                        "metrics", {}
                    ),
                    indent=2,
                    ensure_ascii=False,
                )[:2000])
            except Exception as exc:  # noqa: BLE001
                print(f"[entrypoint] WARN: could not preview metrics: {exc}")


if __name__ == "__main__":
    main()
