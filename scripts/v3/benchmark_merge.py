"""Merge multiple benchmark JSON outputs into one 4-way comparison.

Reads:  artifacts/metrics/benchmark_3way_opf.json + benchmark_mini.json
Writes: artifacts/metrics/benchmark_4way.json

Then run benchmark_reports.py --input benchmark_4way.json to regenerate
all 3 formats (md, csv, html) for the merged set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--inputs", nargs="+", type=Path, required=True,
                    help="JSON files to merge (each must have models dict)")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    merged = {"benchmark": None, "models": {}}
    for path in args.inputs:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if merged["benchmark"] is None:
            merged["benchmark"] = data.get("benchmark")
        for name, payload in data.get("models", {}).items():
            if name in merged["models"]:
                print(f"WARN: model {name} already merged; replacing from {path}")
            merged["models"][name] = payload

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"merged {len(merged['models'])} models from {len(args.inputs)} files → {args.output}")


if __name__ == "__main__":
    main()
