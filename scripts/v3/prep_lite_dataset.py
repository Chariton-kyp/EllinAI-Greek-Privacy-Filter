"""Prepare the v3 Lite finetune dataset.

Combines v2.13 gold train.jsonl with the teacher-pseudo-labelled corpus
into a single OPF-format JSONL ready for `opf train`. Validation, test
and hard_test are reused verbatim from v2.13.

Format normalization:
    - v2.13 gold uses inner key "category" for span labels.
    - v3 pseudo uses "label" (different field name).
    - This script renames pseudo "label" → "category" so the merged
      file is uniform OPF format.
    - Discards records where any span label is OUTSIDE the v2.13 label
      space (defined in configs/label_space.json) — the teacher emits
      a few rare classes (account_number for v3 student models, but
      the v2.13 OPF taxonomy is fixed). This keeps the trainer happy.

Usage:
    python scripts/v3/prep_lite_dataset.py \\
        --gold-train data/processed/aws-v2-XXX/data/train.jsonl \\
        --pseudo /tmp/pseudo_sample.jsonl \\
        --val data/processed/aws-v2-XXX/data/validation.jsonl \\
        --test data/processed/aws-v2-XXX/data/test.jsonl \\
        --hard-test data/processed/aws-v2-XXX/data/hard_test.jsonl \\
        --label-space configs/label_space.json \\
        --output-dir /tmp/v3_lite_data
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path


def load_label_space(path: Path) -> set[str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    # Greek-Privacy-Filter label_space.json schema is
    #   {"span_class_names": ["O", "afm", "amka", ...]}
    if isinstance(data, dict) and "span_class_names" in data:
        labels = set(data["span_class_names"])
        labels.discard("O")  # outside / no-PII tag, not a class
        return labels
    if isinstance(data, dict):
        if "labels" in data:
            return set(data["labels"])
        return set(data.keys())
    if isinstance(data, list):
        return set(data)
    raise SystemExit(f"unrecognised label_space.json shape at {path}")


def normalize_pseudo(pseudo_path: Path, valid_labels: set[str]) -> list[dict]:
    out = []
    drop_label = 0
    drop_empty = 0
    with pseudo_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = rec.get("text", "")
            if not text:
                continue
            spans = rec.get("label", [])
            # Pseudo uses {"label": X, "start":, "end":} — rename to "category"
            renamed: list[dict] = []
            skip_record = False
            for s in spans:
                lbl = s.get("label") or s.get("category")
                if not lbl:
                    continue
                if lbl not in valid_labels:
                    skip_record = True
                    break
                renamed.append({
                    "category": lbl,
                    "start": s["start"],
                    "end": s["end"],
                })
            if skip_record:
                drop_label += 1
                continue
            # Keep records even with empty spans (negative examples)
            out.append({
                "text": text,
                "label": renamed,
                "info": {**rec.get("info", {}), "source": "v3_pseudo"},
            })
    print(f"[pseudo] kept={len(out)} drop_label={drop_label}")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--gold-train", type=Path, required=True)
    p.add_argument("--pseudo", type=Path, required=True)
    p.add_argument("--val", type=Path, required=True)
    p.add_argument("--test", type=Path, required=True)
    p.add_argument("--hard-test", type=Path, required=True)
    p.add_argument("--label-space", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--shuffle-seed", type=int, default=2042)
    p.add_argument("--max-pseudo", type=int, default=None,
                    help="Cap pseudo records (default: all). Useful for fast iteration.")
    p.add_argument("--neg-pos-ratio", type=float, default=3.0,
                    help="Sample N negative pseudo records per positive. Default 3.0. "
                         "Pseudo corpus is ~98%% empty (most Greek text has no PII), "
                         "so without this all-pseudo would skew training to 'always O'.")
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    valid = load_label_space(args.label_space)
    print(f"[label-space] {len(valid)} classes: {sorted(valid)}")

    # Load gold (already in correct format)
    gold = []
    with args.gold_train.open(encoding="utf-8") as f:
        for line in f:
            try:
                gold.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    print(f"[gold] {len(gold)} records")

    # Load + normalize pseudo
    pseudo = normalize_pseudo(args.pseudo, valid)

    # Rebalance: keep all positives, downsample negatives so trainer
    # doesn't learn 'always O'. Pseudo corpus is ~98% empty in
    # natural Greek text — without this, the 100k pseudo dominates
    # the 20k gold (which is 97.5% positive) and flips the dataset
    # to 80% empty → token classifier collapses to majority-class.
    rng = random.Random(args.shuffle_seed)
    pos = [r for r in pseudo if r["label"]]
    neg = [r for r in pseudo if not r["label"]]
    rng.shuffle(neg)
    target_neg = min(len(neg), int(len(pos) * args.neg_pos_ratio))
    pseudo = pos + neg[:target_neg]
    rng.shuffle(pseudo)
    print(f"[pseudo] rebalanced: {len(pos)} positive + {target_neg} negative = {len(pseudo)} total")
    if args.max_pseudo:
        pseudo = pseudo[: args.max_pseudo]
        print(f"[pseudo] capped to {len(pseudo)}")

    # Combine + shuffle (so trainer sees mix per batch)
    combined = gold + pseudo
    random.Random(args.shuffle_seed).shuffle(combined)
    print(f"[combined] {len(combined)} train records ({len(gold)} gold + {len(pseudo)} pseudo)")

    # Write train
    out_train = args.output_dir / "train.jsonl"
    with out_train.open("w", encoding="utf-8") as f:
        for rec in combined:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[write] {out_train}")

    # Copy unchanged splits
    for src, dst_name in [
        (args.val, "validation.jsonl"),
        (args.test, "test.jsonl"),
        (args.hard_test, "hard_test.jsonl"),
    ]:
        dst = args.output_dir / dst_name
        shutil.copy(src, dst)
        n = sum(1 for _ in dst.open(encoding="utf-8"))
        print(f"[copy] {dst}  ({n} records)")


if __name__ == "__main__":
    main()
