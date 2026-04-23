from __future__ import annotations

import argparse
import json
from pathlib import Path


KEYS = [
    "detection.precision",
    "detection.recall",
    "detection.f1",
    "detection.span.precision",
    "detection.span.recall",
    "detection.span.f1",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare baseline vs finetuned OPF metrics files."
    )
    parser.add_argument("--baseline", required=True, help="Baseline metrics JSON path.")
    parser.add_argument("--finetuned", required=True, help="Finetuned metrics JSON path.")
    return parser.parse_args()


def load_metrics(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(f"Invalid OPF metrics payload in {path}")
    return metrics


def metric(metrics: dict[str, float], key: str) -> float:
    value = metrics.get(key, 0.0)
    return float(value)


def main() -> None:
    args = parse_args()
    baseline_metrics = load_metrics(Path(args.baseline))
    finetuned_metrics = load_metrics(Path(args.finetuned))

    print("metric\tbaseline\tfinetuned\tdelta")
    for key in KEYS:
        baseline_value = metric(baseline_metrics, key)
        finetuned_value = metric(finetuned_metrics, key)
        delta = finetuned_value - baseline_value
        print(f"{key}\t{baseline_value:.4f}\t{finetuned_value:.4f}\t{delta:+.4f}")


if __name__ == "__main__":
    main()
