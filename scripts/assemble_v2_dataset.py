"""Assemble a v2 training dataset from a base set of relabelled v1.1
splits plus one or more Tier-1 / Phase-2 record packs.

Inputs:
- A base directory containing the four OPF-format JSONL splits
  (``train.jsonl``, ``validation.jsonl``, ``test.jsonl``,
  ``hard_test.jsonl``). Typically the AFM-relabelled v1.1 dataset
  produced by ``scripts/relabel_afm_spans.py``.
- One or more ``--add`` JSONL files containing supplementary records
  (Tier-1 deterministic records produced by
  ``scripts/generate_tier1_records.py``, future Phase-2 distribution-
  shift records produced by the LLM-driven generators with the new
  Greeklish / polytonic / dialect registers, future Tier-2 quasi-
  identifier records, etc.).

Output:
- ``<output-dir>/{train,validation,test,hard_test}.jsonl`` — the
  unioned, stratified v2 splits.
- ``<output-dir>/assembly_report.json`` — per-class record counts
  per split, dedup statistics, and the full source list.
- (Optional) ``<output-dir>/manifest.json`` if ``--write-manifest``
  is set: SHA-256 + line counts for the four output splits.

Stratification:
- Records added via ``--add`` are first shuffled with the seeded
  RNG and then split per ``--add-train-ratio / --add-val-ratio /
  --add-test-ratio / --add-hard-test-ratio`` (default
  0.80 / 0.10 / 0.05 / 0.05). The ratios must sum to 1.0.
- Stratification is done class-wise: each PII class in the additive
  pack is split independently so every split sees a proportional
  share of every class.

Dedup:
- Exact-text dedup across the entire output (within and across
  splits). When two records share the same ``text`` the first
  occurrence wins; the second is dropped and counted in the report.
- Optional cross-split leakage check: records whose text appears in
  more than one of the v1.1 base splits are reported as a leakage
  warning (these come from the v1.1 inputs and the script does not
  modify them, only flags).

Determinism:
- Re-running the script with the same ``--seed`` and the same input
  files produces byte-identical output.

Usage:

    python scripts/assemble_v2_dataset.py \\
        --base-dir data/processed/v1_1 \\
        --add data/processed/aws-v2-RUN/data/tier1_records.jsonl \\
        --add data/processed/aws-v2-RUN/data/phase2_distribution_shift.jsonl \\
        --output-dir data/processed/v2/combined \\
        --seed 1337 \\
        --write-manifest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SPLIT_NAMES = ["train.jsonl", "validation.jsonl", "test.jsonl", "hard_test.jsonl"]


@dataclass
class AssemblyReport:
    """Aggregate counters for the assembly run."""

    base_dir: str = ""
    add_files: list[str] = field(default_factory=list)
    seed: int = 0
    ratios: dict[str, float] = field(default_factory=dict)
    base_records: dict[str, int] = field(default_factory=dict)
    add_records_total: int = 0
    add_records_per_class: Counter = field(default_factory=Counter)
    add_records_per_split: dict[str, int] = field(default_factory=dict)
    output_records: dict[str, int] = field(default_factory=dict)
    output_classes_per_split: dict[str, dict[str, int]] = field(default_factory=dict)
    text_dedup_dropped: int = 0
    cross_split_leakage_in_base: int = 0


def read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            out.append(json.loads(line))
    return out


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False))
            fh.write("\n")


def primary_class(record: dict) -> str:
    """Return the first label category of the record, or '_no_label'
    if the record has no labels (used for stratification)."""
    labels = record.get("label", [])
    if not labels:
        return "_no_label"
    return labels[0].get("category", "_no_label")


def stratified_split(
    records: list[dict],
    ratios: dict[str, float],
    rng: random.Random,
) -> dict[str, list[dict]]:
    """Split records into named buckets per ratio, stratified by class.

    The same RNG sequence is used for every class, so re-running with
    the same seed and the same input order produces byte-identical
    output.
    """
    by_class: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_class[primary_class(r)].append(r)
    buckets: dict[str, list[dict]] = {name: [] for name in ratios}
    bucket_names = list(ratios.keys())
    bucket_weights = [ratios[name] for name in bucket_names]
    for cls in sorted(by_class):
        cls_records = by_class[cls][:]
        rng.shuffle(cls_records)
        n = len(cls_records)
        # Allocate counts deterministically per bucket: floor of share
        # for each bucket, then distribute the remainder by largest
        # fractional part so totals sum to n exactly.
        raw = [w * n for w in bucket_weights]
        floors = [int(x) for x in raw]
        remainder = n - sum(floors)
        fracs = sorted(
            range(len(bucket_names)),
            key=lambda i: (floors[i] - raw[i], i),
        )
        for i in fracs[:remainder]:
            floors[i] += 1
        cursor = 0
        for name, count in zip(bucket_names, floors):
            buckets[name].extend(cls_records[cursor : cursor + count])
            cursor += count
    # Final shuffle within each bucket to mix classes.
    for name in buckets:
        rng.shuffle(buckets[name])
    return buckets


def dedup_records(
    records: list[dict], seen_texts: set[str]
) -> tuple[list[dict], int]:
    """Drop records whose text is already in ``seen_texts``. Returns
    (kept, dropped_count). ``seen_texts`` is updated in place with
    the kept records' texts."""
    kept: list[dict] = []
    dropped = 0
    for r in records:
        t = r.get("text", "")
        if t in seen_texts:
            dropped += 1
            continue
        seen_texts.add(t)
        kept.append(r)
    return kept, dropped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--base-dir",
        type=Path,
        required=True,
        help=(
            "Directory containing the four OPF-format JSONL base splits "
            "(train.jsonl, validation.jsonl, test.jsonl, hard_test.jsonl). "
            "Typically the v1.1 relabelled directory."
        ),
    )
    parser.add_argument(
        "--add",
        action="append",
        default=[],
        type=Path,
        help=(
            "Supplementary JSONL pack to merge into the base splits. "
            "May be passed multiple times (e.g. --add tier1.jsonl "
            "--add phase2_dist.jsonl)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write the assembled splits + reports.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="RNG seed for shuffles + stratification.",
    )
    parser.add_argument(
        "--add-train-ratio",
        type=float,
        default=0.80,
        help="Share of additive records to route into train.jsonl.",
    )
    parser.add_argument(
        "--add-val-ratio",
        type=float,
        default=0.10,
        help="Share of additive records to route into validation.jsonl.",
    )
    parser.add_argument(
        "--add-test-ratio",
        type=float,
        default=0.05,
        help="Share of additive records to route into test.jsonl.",
    )
    parser.add_argument(
        "--add-hard-test-ratio",
        type=float,
        default=0.05,
        help="Share of additive records to route into hard_test.jsonl.",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help=(
            "Write a SHA-256 manifest of the four output splits to "
            "<output-dir>/manifest.json. Off by default; turn on for "
            "audit-evidence runs."
        ),
    )
    return parser.parse_args()


def validate_ratios(args: argparse.Namespace) -> dict[str, float]:
    ratios = {
        "train.jsonl": args.add_train_ratio,
        "validation.jsonl": args.add_val_ratio,
        "test.jsonl": args.add_test_ratio,
        "hard_test.jsonl": args.add_hard_test_ratio,
    }
    total = sum(ratios.values())
    if abs(total - 1.0) > 1e-6:
        raise SystemExit(
            f"--add-* ratios must sum to 1.0; got {total}"
        )
    return ratios


def main() -> int:
    args = parse_args()
    ratios = validate_ratios(args)
    rng = random.Random(args.seed)
    base_dir: Path = args.base_dir.expanduser().resolve()
    output_dir: Path = args.output_dir.expanduser().resolve()
    if not base_dir.is_dir():
        print(f"FAIL: base dir not found: {base_dir}", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    report = AssemblyReport(
        base_dir=str(base_dir),
        add_files=[str(p) for p in args.add],
        seed=args.seed,
        ratios=ratios,
    )

    # 1. Load base splits.
    base_splits: dict[str, list[dict]] = {}
    base_split_texts: dict[str, set[str]] = {}
    for split_name in SPLIT_NAMES:
        in_path = base_dir / split_name
        if not in_path.is_file():
            print(f"FAIL: base split missing: {in_path}", file=sys.stderr)
            return 1
        recs = read_jsonl(in_path)
        base_splits[split_name] = recs
        base_split_texts[split_name] = set(r.get("text", "") for r in recs)
        report.base_records[split_name] = len(recs)
    print(f"[assemble] base loaded: " + ", ".join(
        f"{k}={v}" for k, v in report.base_records.items()
    ))

    # 1b. Cross-split leakage check inside the base (informational).
    seen_globally: dict[str, str] = {}
    for split_name, txts in base_split_texts.items():
        for t in txts:
            if t in seen_globally and seen_globally[t] != split_name:
                report.cross_split_leakage_in_base += 1
            seen_globally.setdefault(t, split_name)
    if report.cross_split_leakage_in_base:
        print(
            f"[assemble] WARN: {report.cross_split_leakage_in_base} records appear in "
            f"more than one base split (carried through unchanged)"
        )

    # 2. Load + stratify each --add file.
    add_records: list[dict] = []
    for add_path in args.add:
        p = add_path.expanduser().resolve()
        if not p.is_file():
            print(f"FAIL: --add file not found: {p}", file=sys.stderr)
            return 1
        recs = read_jsonl(p)
        add_records.extend(recs)
        for r in recs:
            report.add_records_per_class[primary_class(r)] += 1
        print(f"[assemble] add loaded: {p} ({len(recs)} records)")
    report.add_records_total = len(add_records)

    add_buckets = stratified_split(add_records, ratios, rng) if add_records else {
        n: [] for n in SPLIT_NAMES
    }
    for split_name in SPLIT_NAMES:
        report.add_records_per_split[split_name] = len(add_buckets.get(split_name, []))

    # 3. Merge each split with dedup against everything seen so far.
    final_splits: dict[str, list[dict]] = {}
    seen_texts: set[str] = set()
    for split_name in SPLIT_NAMES:
        merged = base_splits[split_name][:] + add_buckets.get(split_name, [])
        kept, dropped = dedup_records(merged, seen_texts)
        report.text_dedup_dropped += dropped
        final_splits[split_name] = kept
        report.output_records[split_name] = len(kept)
        cls_counter: Counter = Counter()
        for r in kept:
            for lab in r.get("label", []):
                cls_counter[lab.get("category", "_unlabelled")] += 1
        report.output_classes_per_split[split_name] = dict(cls_counter)

    # 4. Write outputs.
    for split_name, recs in final_splits.items():
        write_jsonl(recs, output_dir / split_name)
    print(f"[assemble] wrote: " + ", ".join(
        f"{k}={v}" for k, v in report.output_records.items()
    ))

    # 5. Optional manifest.
    if args.write_manifest:
        manifest_entries = []
        for split_name in SPLIT_NAMES:
            p = output_dir / split_name
            data = p.read_bytes()
            manifest_entries.append({
                "path": split_name,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "line_count": sum(1 for _ in p.open(encoding="utf-8")),
            })
        manifest = {
            "manifest_version": "v2_combined",
            "base_dir": str(base_dir),
            "add_files": [str(p) for p in args.add],
            "seed": args.seed,
            "ratios": ratios,
            "entries": manifest_entries,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[assemble] manifest: {output_dir / 'manifest.json'}")

    # 6. Always write report.
    report_path = output_dir / "assembly_report.json"
    report_path.write_text(
        json.dumps(
            {
                "base_dir": report.base_dir,
                "add_files": report.add_files,
                "seed": report.seed,
                "ratios": report.ratios,
                "base_records": report.base_records,
                "add_records_total": report.add_records_total,
                "add_records_per_class": dict(report.add_records_per_class),
                "add_records_per_split": report.add_records_per_split,
                "output_records": report.output_records,
                "output_classes_per_split": report.output_classes_per_split,
                "text_dedup_dropped": report.text_dedup_dropped,
                "cross_split_leakage_in_base": report.cross_split_leakage_in_base,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[assemble] report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
