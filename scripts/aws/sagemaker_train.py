"""Launch a Greek Privacy Filter fine-tuning job on AWS SageMaker.

See scripts/aws/README.md for full setup instructions.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import sagemaker
    from sagemaker.pytorch import PyTorch
except ImportError as exc:
    raise SystemExit(
        "sagemaker SDK not installed. Run: pip install 'sagemaker>=2.224' boto3"
    ) from exc

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, help="IAM role ARN for SageMaker.")
    parser.add_argument("--bucket", required=True, help="S3 bucket name (no s3://).")
    parser.add_argument("--prefix", default="greek-privacy-filter")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--instance-type", default="ml.g5.xlarge")
    parser.add_argument("--use-spot", action="store_true")
    parser.add_argument("--max-run", type=int, default=3 * 3600)
    parser.add_argument("--max-wait", type=int, default=6 * 3600)
    parser.add_argument("--job-name", default=None)

    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum-steps", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--n-ctx", type=int, default=256)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument(
        "--output-param-dtype",
        choices=("inherit", "bf16", "fp32"), default="bf16",
    )
    parser.add_argument("--framework-version", default="2.3.0")
    parser.add_argument("--py-version", default="py311")
    parser.add_argument("--skip-test-eval", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _s3(bucket: str, prefix: str, *parts: str) -> str:
    key = "/".join(p.strip("/") for p in (prefix, *parts))
    return f"s3://{bucket}/{key}"


def main() -> None:
    args = parse_args()

    sess = None
    if not args.dry_run:
        import boto3
        boto_session = boto3.Session(region_name=args.region)
        sess = sagemaker.Session(
            boto_session=boto_session, default_bucket=args.bucket
        )

    data_prefix = f"{args.prefix}/data"
    ckpt_prefix = f"{args.prefix}/checkpoint"
    output_s3 = _s3(args.bucket, args.prefix, "output")

    inputs = {
        "train":      _s3(args.bucket, data_prefix, "train"),
        "validation": _s3(args.bucket, data_prefix, "validation"),
        "test":       _s3(args.bucket, data_prefix, "test"),
        "labels":     _s3(args.bucket, data_prefix, "labels"),
        "checkpoint": _s3(args.bucket, ckpt_prefix),
    }

    hyperparameters = {
        "epochs": args.epochs,
        "batch-size": args.batch_size,
        "grad-accum-steps": args.grad_accum_steps,
        "learning-rate": args.learning_rate,
        "n-ctx": args.n_ctx,
        "seed": args.seed,
        "output-param-dtype": args.output_param_dtype,
    }
    if args.skip_test_eval:
        hyperparameters["skip-test-eval"] = ""

    source_dir = str(PROJECT_ROOT)

    estimator = None
    if not args.dry_run:
        estimator = PyTorch(
            entry_point="scripts/aws/entrypoint.py",
            source_dir=source_dir,
            role=args.role,
            instance_count=1,
            instance_type=args.instance_type,
            framework_version=args.framework_version,
            py_version=args.py_version,
            hyperparameters=hyperparameters,
            output_path=output_s3,
            base_job_name=args.job_name or "greek-pf-ft",
            use_spot_instances=args.use_spot,
            max_run=args.max_run,
            max_wait=args.max_wait if args.use_spot else None,
            sagemaker_session=sess,
            dependencies=[],
            environment={"PYTHONHASHSEED": str(args.seed)},
        )

    print("=== SageMaker Training Job ===")
    print(f"  region:          {args.region}")
    print(f"  instance:        {args.instance_type} (spot={args.use_spot})")
    print(f"  role:            {args.role}")
    print(f"  output:          {output_s3}")
    print("  inputs:")
    for k, v in inputs.items():
        print(f"    {k:<11} -> {v}")
    print(f"  hyperparameters: {hyperparameters}")

    if args.dry_run:
        print("[dry-run] Not calling estimator.fit().")
        return

    assert estimator is not None
    estimator.fit(inputs=inputs, wait=True, logs="All")
    print(f"Model artifacts: {estimator.model_data}")


if __name__ == "__main__":
    sys.exit(main())
