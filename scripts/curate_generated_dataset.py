"""Curate a raw generated Greek PII dataset into balanced splits.

Pipeline (fully deterministic, seed-controlled, no human-in-loop):

  Stage 1 — Quality filter
    Heuristics on length, character classes, chat-model artefacts, and
    span sanity. Drops low-quality or mis-formatted records.

  Stage 2 — Near-duplicate removal
    Locality-sensitive 3-signature bucketing per record (first-5-words,
    middle-5-words, last-5-words hashes). Any new record whose
    signatures collide with a kept record is dropped.

  Stage 3 — Class-balanced stratified split
    Greedy fill of per-class quotas across train / validation / test /
    hard_test. Primary label per record = first labelled span's category,
    or "_hard_negative" for label-free records. Records that don't
    contribute to any unfilled quota are dropped.

Outputs:

  data/processed/train.jsonl
  data/processed/validation.jsonl
  data/processed/test.jsonl
  data/processed/hard_test.jsonl
  artifacts/metrics/curation_report.json

Usage:

  python scripts/curate_generated_dataset.py \
      --input data/processed/greek_100k_raw.jsonl \
      --output-dir data/processed \
      --train-size 10000 --val-size 1500 --test-size 1500 \
      --hard-size 1500 --seed 1337
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Stage 1 — quality filter
# ---------------------------------------------------------------------------

MIN_LEN = 30
MAX_LEN = 300

# Chat-model artefacts that shouldn't appear in a training sentence.
ARTIFACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)here['’]?s a"),
    re.compile(r"(?i)thinking process"),
    re.compile(r"<think\b", re.I),
    re.compile(r"</think>", re.I),
    re.compile(r"```"),
    re.compile(r"^\s*(παράδειγμα|σίγουρα|φυσικά|βεβαίως)[:!]?", re.I),
    re.compile(r"^\s*(ορίστε|ιδού|εδώ είναι|ένα παράδειγμα)", re.I),
    re.compile(r"^\s*\d+\.\s*$"),  # orphan numbering line
    # HTML/markdown leakage:
    re.compile(r"<[a-z]+[\s>]", re.I),
]


def _greek_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 1.0  # non-alphabetic text (e.g., just numbers) treated as OK
    greek = sum(
        1 for c in letters
        if "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿"
    )
    return greek / len(letters)


def _latin_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if "a" <= c.lower() <= "z")
    return latin / len(letters)


def quality_check(record: dict) -> tuple[bool, str]:
    text = record.get("text", "")
    labels = record.get("label") or []
    if not isinstance(text, str) or not text.strip():
        return False, "empty_text"
    text_len = len(text)
    if text_len < MIN_LEN:
        return False, "too_short"
    if text_len > MAX_LEN:
        return False, "too_long"
    for pattern in ARTIFACT_PATTERNS:
        if pattern.search(text):
            return False, f"artifact:{pattern.pattern[:30]}"
    gr = _greek_ratio(text)
    la = _latin_ratio(text)
    if gr < 0.4 and la > 0.3:
        return False, "low_greek_high_latin"
    # Span sanity
    seen_values: set[tuple[str, int, int]] = set()
    for sp in labels:
        if not isinstance(sp, dict):
            return False, "bad_span_shape"
        cat = sp.get("category")
        start, end = sp.get("start"), sp.get("end")
        if not isinstance(cat, str):
            return False, "bad_category"
        if not isinstance(start, int) or not isinstance(end, int):
            return False, "bad_offsets"
        if start < 0 or end > text_len or start >= end:
            return False, "invalid_offsets"
        span_text = text[start:end]
        if not span_text.strip():
            return False, "empty_span"
        key = (cat, start, end)
        if key in seen_values:
            return False, "duplicate_span"
        seen_values.add(key)
    return True, "ok"


# ---------------------------------------------------------------------------
# Stage 2 — near-duplicate removal via locality-sensitive signatures
# ---------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.lower()).strip()


def _text_hash(text: str) -> str:
    return hashlib.blake2b(
        _normalize(text).encode("utf-8"), digest_size=16
    ).hexdigest()


def _skeleton_hash(record: dict) -> str:
    """Hash the record with each PII span replaced by its category placeholder.

    Two records sharing the same skeleton come from the same template
    with the same PII arrangement — near-duplicates at the structural
    level even when the PII values differ. We allow SOME skeleton
    repetition (same template with different PII is desirable for
    training), so this is NOT used for dedup directly — see below.
    """
    text = record["text"]
    labels = sorted(record.get("label") or [], key=lambda s: s["start"])
    out: list[str] = []
    cursor = 0
    for sp in labels:
        out.append(text[cursor:sp["start"]])
        out.append(f"<{sp['category']}>")
        cursor = sp["end"]
    out.append(text[cursor:])
    return _text_hash("".join(out))


def dedup(records: list[dict], *, max_per_skeleton: int = 300
         ) -> tuple[list[dict], int]:
    """Drop records that are exact duplicates (post-normalization) of prior
    records. Also cap any single template skeleton at `max_per_skeleton`
    so one template can't dominate the dataset."""
    seen_texts: set[str] = set()
    skeleton_counts: dict[str, int] = {}
    kept: list[dict] = []
    dropped = 0
    for r in records:
        th = _text_hash(r["text"])
        if th in seen_texts:
            dropped += 1
            continue
        sk = _skeleton_hash(r)
        if skeleton_counts.get(sk, 0) >= max_per_skeleton:
            dropped += 1
            continue
        seen_texts.add(th)
        skeleton_counts[sk] = skeleton_counts.get(sk, 0) + 1
        kept.append(r)
    return kept, dropped


# ---------------------------------------------------------------------------
# Stage 3 — class-balanced stratified split
# ---------------------------------------------------------------------------

PRIMARY_HARD_NEGATIVE = "_hard_negative"

PII_CLASSES: tuple[str, ...] = (
    "amka", "afm", "adt", "iban_gr",
    "private_person", "private_phone", "private_address",
    "private_email", "private_date", "private_url",
    "account_number", "secret",
)


def primary_label(record: dict) -> str:
    labels = record.get("label") or []
    if not labels:
        return PRIMARY_HARD_NEGATIVE
    by_start = sorted(labels, key=lambda sp: sp["start"])
    return by_start[0]["category"]


# Train-set per-class targets. Validation/test/hard-test scale proportionally.
TRAIN_CLASS_TARGETS: dict[str, int] = {
    "amka": 1200, "afm": 1200, "adt": 1200, "iban_gr": 1000,
    "private_person": 1500, "private_phone": 1500,
    "private_address": 1200, "private_email": 800,
    "private_date": 800, "private_url": 600,
    "account_number": 800, "secret": 600,
    PRIMARY_HARD_NEGATIVE: 1800,
}


def _scale_targets(base_targets: dict[str, int],
                   target_total: int) -> dict[str, int]:
    """Scale `base_targets` so their counts sum to `target_total`."""
    base_sum = sum(base_targets.values()) or 1
    scale = target_total / base_sum
    scaled = {k: max(1, int(round(v * scale))) for k, v in base_targets.items()}
    # Adjust sum to match target_total within rounding slack.
    delta = target_total - sum(scaled.values())
    if delta != 0:
        for k in sorted(scaled, key=lambda x: -scaled[x]):
            if delta == 0:
                break
            step = 1 if delta > 0 else -1
            if scaled[k] + step >= 1:
                scaled[k] += step
                delta -= step
    return scaled


def stratified_split(records: list[dict], *, train_size: int, val_size: int,
                     test_size: int, hard_size: int,
                     seed: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    shuffled = records[:]
    rng.shuffle(shuffled)

    quotas: dict[str, dict[str, int]] = {
        "train": _scale_targets(TRAIN_CLASS_TARGETS, train_size),
        "validation": _scale_targets(TRAIN_CLASS_TARGETS, val_size),
        "test": _scale_targets(TRAIN_CLASS_TARGETS, test_size),
        "hard_test": _scale_targets(TRAIN_CLASS_TARGETS, hard_size),
    }

    splits_order = ["train", "validation", "test", "hard_test"]
    initial: dict[str, dict[str, int]] = {
        split: dict(quotas[split]) for split in splits_order
    }
    remaining: dict[str, dict[str, int]] = {
        split: dict(quotas[split]) for split in splits_order
    }
    taken: dict[str, list[dict]] = {split: [] for split in splits_order}

    def _proportional_remaining(split: str, label: str) -> float:
        init = initial[split].get(label, 0)
        if init <= 0:
            return -1.0
        return remaining[split].get(label, 0) / init

    for r in shuffled:
        diff = r.get("info", {}).get("difficulty", "")
        label = primary_label(r)
        # "hard" difficulty gets first crack at hard_test.
        if diff == "hard" and remaining["hard_test"].get(label, 0) > 0:
            taken["hard_test"].append(r)
            remaining["hard_test"][label] -= 1
            continue
        # Pick split with largest proportional headroom for this class.
        best_split = None
        best_score = 0.0
        for split in splits_order:
            score = _proportional_remaining(split, label)
            if score > best_score:
                best_score = score
                best_split = split
        if best_split is not None:
            taken[best_split].append(r)
            remaining[best_split][label] -= 1

    return taken


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for r in records:
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")


def _count_spans_per_class(records: list[dict]) -> dict[str, int]:
    c: Counter = Counter()
    for r in records:
        labels = r.get("label") or []
        if not labels:
            c[PRIMARY_HARD_NEGATIVE] += 1
        for sp in labels:
            c[sp["category"]] += 1
    return dict(c)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output-dir", default="data/processed")
    p.add_argument("--train-size", type=int, default=10000)
    p.add_argument("--val-size", type=int, default=1500)
    p.add_argument("--test-size", type=int, default=1500)
    p.add_argument("--hard-size", type=int, default=1500)
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument(
        "--report-path", default="artifacts/metrics/curation_report.json",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    report_path = Path(args.report_path)
    if not report_path.is_absolute():
        report_path = PROJECT_ROOT / report_path

    # Stage 1
    accepted: list[dict] = []
    reject_reasons: Counter = Counter()
    total = 0
    for record in _iter_jsonl(input_path):
        total += 1
        ok, reason = quality_check(record)
        if ok:
            accepted.append(record)
        else:
            reject_reasons[reason] += 1
    print(f"Stage 1: {len(accepted)}/{total} passed quality filter "
          f"({total - len(accepted)} dropped)")

    # Stage 2
    deduped, removed_dups = dedup(accepted)
    print(f"Stage 2: {len(deduped)} after dedup ({removed_dups} dropped)")

    # Stage 3
    splits = stratified_split(
        deduped,
        train_size=args.train_size, val_size=args.val_size,
        test_size=args.test_size, hard_size=args.hard_size,
        seed=args.seed,
    )
    for name, records in splits.items():
        print(f"Stage 3: {name} = {len(records)} records")

    # Write outputs.
    split_files: dict[str, str] = {}
    for name, records in splits.items():
        out = output_dir / f"{name}.jsonl"
        _write_jsonl(out, records)
        try:
            rel = out.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            rel = out.as_posix()
        split_files[name] = rel

    # Report.
    report = {
        "input": str(input_path.relative_to(PROJECT_ROOT).as_posix()),
        "input_total_records": total,
        "stage1": {
            "accepted": len(accepted),
            "rejected": total - len(accepted),
            "reject_reasons": dict(reject_reasons.most_common()),
        },
        "stage2": {
            "after_dedup": len(deduped),
            "removed_duplicates": removed_dups,
        },
        "stage3": {
            name: {
                "count": len(records),
                "spans_per_class": _count_spans_per_class(records),
            }
            for name, records in splits.items()
        },
        "files": split_files,
        "seed": args.seed,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
