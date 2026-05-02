"""Verify per-record provenance on every dataset split.

Audits that every JSONL record carries the `info` metadata this
repository stamps at generation time and that the values fall into the
known vocabulary. Reports any missing / unexpected values.

Intended to run before uploading an artefact to S3 or publishing a
release, so the dataset ships with a clean provenance manifest.

Usage:

    python scripts/verify_provenance.py \
        --inputs data/processed/train.jsonl data/processed/validation.jsonl \
                 data/processed/test.jsonl data/processed/hard_test.jsonl \
        --report-path artifacts/metrics/provenance_report.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


KNOWN_STRATEGIES = {
    "templates",
    "carrier",
    "hard_negative",
    "qwen_hard_negative",
}
KNOWN_STRATEGY_PREFIXES = (
    "ollama/",      # e.g. ollama/<model>/batch, ollama/<model>/slot
    "llm-server/",  # e.g. llm-server/<model>/batch, llm-server/<model>/slot
)

KNOWN_SOURCES = {
    "commercial_safe_generator",
    "golden_seeds",
    "local_qwen_contrastive_v2_13",
}

KNOWN_DIFFICULTIES = {"easy", "medium", "hard", "hard_negative"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", nargs="+", required=True)
    p.add_argument(
        "--report-path", default="artifacts/metrics/provenance_report.json",
    )
    return p.parse_args()


def _audit_file(path: Path) -> dict:
    strategy: Counter = Counter()
    source: Counter = Counter()
    difficulty: Counter = Counter()
    missing_info = 0
    unknown_strategy = 0
    unknown_source = 0
    unknown_difficulty = 0
    total = 0
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            total += 1
            record = json.loads(line)
            info = record.get("info")
            if not isinstance(info, dict):
                missing_info += 1
                continue
            st = info.get("strategy", "")
            sr = info.get("source", "")
            df = info.get("difficulty", "")
            strategy[st] += 1
            source[sr] += 1
            difficulty[df] += 1
            if (
                st not in KNOWN_STRATEGIES
                and not any(st.startswith(p) for p in KNOWN_STRATEGY_PREFIXES)
            ):
                unknown_strategy += 1
            if sr not in KNOWN_SOURCES:
                unknown_source += 1
            if df not in KNOWN_DIFFICULTIES:
                unknown_difficulty += 1
    return {
        "total": total,
        "missing_info": missing_info,
        "unknown_strategy": unknown_strategy,
        "unknown_source": unknown_source,
        "unknown_difficulty": unknown_difficulty,
        "strategies": dict(strategy.most_common()),
        "sources": dict(source.most_common()),
        "difficulties": dict(difficulty.most_common()),
    }


def main() -> None:
    args = parse_args()
    report: dict = {"files": {}}
    all_clean = True
    for item in args.inputs:
        path = Path(item)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            print(f"MISSING: {path}")
            all_clean = False
            continue
        res = _audit_file(path)
        report["files"][str(path.relative_to(PROJECT_ROOT).as_posix())] = res
        bad = (
            res["missing_info"]
            + res["unknown_strategy"]
            + res["unknown_source"]
            + res["unknown_difficulty"]
        )
        status = "OK" if bad == 0 else f"{bad} issues"
        print(f"{path.name}: {res['total']} records, {status}")
        if bad:
            all_clean = False
    out = Path(args.report_path)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)
    print(f"Report: {out}")
    if not all_clean:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
