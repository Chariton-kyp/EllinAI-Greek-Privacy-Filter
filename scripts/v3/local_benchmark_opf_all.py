"""Run the Greek PII Public Benchmark v1 against ALL local OPF-based models.

Covers the full v2 iteration ladder + v3 Lite students, so we can see the
progression v2 -> v2.13 and where Lite stands, on the public benchmark.

Reuses the triage/eval logic from local_benchmark_opf_3way.py.

Output: artifacts/metrics/benchmark_opf_all.json (mergeable into reports).

Usage (inside gpf-inference container):
    docker compose run --rm gpf-benchmark \\
        python /workspace/scripts/v3/local_benchmark_opf_all.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from local_benchmark_opf_3way import evaluate_model  # noqa: E402

DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "greek_pii_public_v1" / "cases.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "metrics" / "benchmark_opf_all.json"

ART = PROJECT_ROOT / "artifacts"

# Ordered so the report reads as a progression.
ALL_MODELS = {
    "opf_base": PROJECT_ROOT / "checkpoints" / "base" / "privacy-filter",
    "v2":       ART / "finetune-v2-20260428T134618Z" / "model",
    "v2_5":     ART / "finetune-v2-5-20260428T184957Z" / "model",
    "v2_6":     ART / "finetune-v2-6-20260428T201919Z" / "model",
    "v2_7":     ART / "finetune-v2-7-20260429T080840Z" / "model",
    "v2_8":     ART / "finetune-v2-8-20260429T095934Z" / "model",
    "v2_9":     ART / "finetune-v2-9-20260429T133121Z" / "model",
    "v2_10":    ART / "finetune-v2-10-20260429T154853Z" / "model",
    "v2_11":    ART / "finetune-v2-11-20260430T072554Z" / "model",
    "v2_12":    ART / "finetune-v2-12-20260430T094120Z" / "model",
    "v2_13":    ART / "finetune-v2-13-20260501T202431Z" / "model",
    "lite":     ART / "v3" / "students" / "lite-local",
    "lite_v3":  ART / "v3" / "students" / "lite-v3-local",
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--models", nargs="*", default=list(ALL_MODELS.keys()))
    args = p.parse_args()

    cases: list[dict] = []
    with args.benchmark.open(encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))
    print(f"loaded {len(cases)} cases from {args.benchmark}", flush=True)

    results: dict = {"benchmark": str(args.benchmark), "models": {}}
    for name in args.models:
        if name not in ALL_MODELS:
            print(f"WARN: unknown model {name}, skipping", flush=True)
            continue
        ckpt = ALL_MODELS[name]
        if not (ckpt / "model.safetensors").exists():
            print(f"WARN: {name} weights missing at {ckpt}, skipping", flush=True)
            continue
        try:
            print(f"\n===== {name} =====", flush=True)
            results["models"][name] = evaluate_model(name, ckpt, cases)
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] FATAL: {e}", flush=True)
            results["models"][name] = {"error": str(e)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {args.output}")

    print("\n=== Summary (untyped F1 / typed F1) ===")
    for name, r in results["models"].items():
        if "error" in r:
            print(f"  {name:<10s}  ERROR: {r['error']}")
            continue
        a = r["aggregate"]
        print(f"  {name:<10s}  untyped F1 = {a['untyped']['f1']:.4f}  "
              f"typed F1 = {a['typed']['f1']:.4f}  ({a['elapsed_seconds']:.1f}s)")


if __name__ == "__main__":
    main()
