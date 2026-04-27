"""Deterministic AFM-span boundary cleaner for OPF training JSONL files.

The Greek tax-identifier (``afm``) is a 9-digit number. v1 of this
project's training corpus accumulated boundary noise from the upstream
LLM generator: a 74% share of AFM spans included a label-prefix word
inside the span (``ΑΦΜ ``, ``Α.Φ.Μ.: ``, ``EL`` for the EU-VAT
form, etc.). Span F1 measured under that convention rewards the model
for learning the prefix as part of the value, which is wrong: real-
world deployment expects the span to contain digits only.

This script reads OPF-format JSONL splits, finds every span labelled
``afm``, and rewrites the span boundaries so they cover **the 9-digit
value only** — never a prefix word, never the surrounding whitespace
or punctuation, never the EU-VAT ``EL`` country code. The other span
classes are passed through unchanged. Output JSONL files are byte-
identical to inputs except for the corrected ``label[].start`` and
``label[].end`` integers on AFM spans.

Idempotent: running the script twice on the same input produces the
same output. Records whose AFM spans cannot be reduced to exactly 9
digits (e.g. a span that contains 10 digits, or none) are left
unmodified and logged in the run report.

Usage:

    python scripts/relabel_afm_spans.py \\
        --input-dir data/processed/aws-v1-20260426T092703Z/data \\
        --output-dir data/processed/v1_1 \\
        --report data/processed/v1_1/relabel_report.json

The output directory and the report path live under
``data/processed/`` which is gitignored, matching the convention used
by the AWS spot launchers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Recognised AFM-prefix tokens, in priority order. Longer tokens come
# first so that a span like "Α.Φ.Μ.: 234567890" is matched against
# the full "Α.Φ.Μ.:" rather than the substring "Α.Φ.Μ.". The match
# is anchored to the start of the span only.
AFM_PREFIX_TOKENS = [
    "Α.Φ.Μ.:",
    "Α.Φ.Μ.",
    "ΑΦΜ:",
    "ΑΦΜ.",
    "ΑΦΜ",
    "AFM:",
    "AFM.",
    "AFM",
    "VAT:",
    "VAT",
    "EL",  # EU-VAT country-code prefix attached directly to digits, e.g. "EL234567890"
]

# Span shape: optional prefix token, optional whitespace / punctuation,
# then exactly 9 digits, then optional trailing whitespace.
_PREFIX_ALT = "|".join(re.escape(p) for p in AFM_PREFIX_TOKENS)
AFM_SPAN_RE = re.compile(
    rf"^\s*(?:(?:{_PREFIX_ALT})[\s:.\-]*)?(?P<digits>[0-9]{{9}})\s*$"
)


@dataclass
class SplitReport:
    """Per-split counters for the relabel run."""

    records_total: int = 0
    afm_spans_total: int = 0
    afm_spans_already_clean: int = 0
    afm_spans_relabelled: int = 0
    afm_spans_unparseable: int = 0
    unparseable_samples: list[str] = field(default_factory=list)
    relabel_shape_counts: Counter = field(default_factory=Counter)


@dataclass
class RunReport:
    """Aggregate report across all processed splits."""

    splits: dict[str, SplitReport] = field(default_factory=dict)


def relabel_afm_span(
    text: str, start: int, end: int
) -> tuple[int, int] | None:
    """Return (new_start, new_end) covering the 9-digit AFM value only.

    Returns ``None`` if the input span cannot be reduced to exactly 9
    digits (e.g. it contains 10 digits, has a non-recognised prefix
    that prevents matching, or has interior whitespace inside the
    digit run).
    """
    span = text[start:end]
    m = AFM_SPAN_RE.match(span)
    if not m:
        return None
    digit_offset = m.start("digits")
    new_start = start + digit_offset
    new_end = new_start + 9
    # Final sanity: the new boundaries must extract exactly 9 ASCII
    # digits from the source text.
    new_span = text[new_start:new_end]
    if len(new_span) != 9 or not new_span.isdigit():
        return None
    return new_start, new_end


def shape_of(span: str) -> str:
    """Return a coarse shape string for an AFM span, used to bucket
    the relabel-source distribution in the report.
    """
    out: list[str] = []
    i = 0
    while i < len(span):
        ch = span[i]
        if ch.isdigit():
            j = i
            while j < len(span) and span[j].isdigit():
                j += 1
            out.append(f"d{j - i}")
            i = j
        elif ch.isalpha():
            j = i
            cls = "A" if ch.isupper() else "a"
            while j < len(span) and span[j].isalpha() and (
                ("A" if span[j].isupper() else "a") == cls
            ):
                j += 1
            out.append(f"{cls}{j - i}")
            i = j
        elif ch == " ":
            out.append(" ")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def relabel_record(
    record: dict, split_report: SplitReport
) -> dict:
    """Return a new record with cleaned AFM span boundaries.

    Mutates the per-split report counters as a side effect. The
    original record is not modified.
    """
    text: str = record["text"]
    new_labels: list[dict] = []
    for lab in record.get("label", []):
        new_lab = dict(lab)
        if lab.get("category") != "afm":
            new_labels.append(new_lab)
            continue
        split_report.afm_spans_total += 1
        start = int(lab["start"])
        end = int(lab["end"])
        original_span = text[start:end]
        if (
            len(original_span) == 9
            and original_span.isdigit()
        ):
            split_report.afm_spans_already_clean += 1
            new_labels.append(new_lab)
            continue
        cleaned = relabel_afm_span(text, start, end)
        if cleaned is None:
            split_report.afm_spans_unparseable += 1
            if len(split_report.unparseable_samples) < 10:
                split_report.unparseable_samples.append(original_span)
            new_labels.append(new_lab)
            continue
        new_start, new_end = cleaned
        new_lab["start"] = new_start
        new_lab["end"] = new_end
        split_report.afm_spans_relabelled += 1
        split_report.relabel_shape_counts[shape_of(original_span)] += 1
        new_labels.append(new_lab)
    new_record = dict(record)
    new_record["label"] = new_labels
    return new_record


def relabel_split(
    input_path: Path, output_path: Path, run_report: RunReport
) -> None:
    """Stream a JSONL split through the relabeller and write the result."""
    split_name = input_path.name
    split_report = SplitReport()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open(encoding="utf-8") as fh_in, \
            output_path.open("w", encoding="utf-8") as fh_out:
        for line in fh_in:
            line = line.rstrip("\n")
            if not line:
                continue
            record = json.loads(line)
            split_report.records_total += 1
            new_record = relabel_record(record, split_report)
            fh_out.write(json.dumps(new_record, ensure_ascii=False))
            fh_out.write("\n")
    run_report.splits[split_name] = split_report


def write_report(run_report: RunReport, report_path: Path) -> None:
    payload = {}
    for split_name, sr in run_report.splits.items():
        payload[split_name] = {
            "records_total": sr.records_total,
            "afm_spans_total": sr.afm_spans_total,
            "afm_spans_already_clean": sr.afm_spans_already_clean,
            "afm_spans_relabelled": sr.afm_spans_relabelled,
            "afm_spans_unparseable": sr.afm_spans_unparseable,
            "afm_spans_clean_after_relabel_pct": (
                round(
                    100.0
                    * (sr.afm_spans_already_clean + sr.afm_spans_relabelled)
                    / sr.afm_spans_total,
                    2,
                )
                if sr.afm_spans_total
                else None
            ),
            "unparseable_samples": sr.unparseable_samples,
            "relabel_shape_counts": dict(sr.relabel_shape_counts),
        }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing the OPF JSONL split files to relabel.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory to write the relabelled JSONL split files.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train.jsonl", "validation.jsonl", "test.jsonl", "hard_test.jsonl"],
        help="Split filenames to process (relative to input-dir).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help=(
            "Path to write the JSON relabel report. Defaults to "
            "<output-dir>/relabel_report.json."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir: Path = args.input_dir.expanduser().resolve()
    output_dir: Path = args.output_dir.expanduser().resolve()
    if not input_dir.is_dir():
        print(f"FAIL: input dir not found: {input_dir}", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    run_report = RunReport()
    for split_name in args.splits:
        in_path = input_dir / split_name
        if not in_path.is_file():
            print(f"WARN: split missing, skipping: {in_path}", file=sys.stderr)
            continue
        out_path = output_dir / split_name
        print(f"[relabel] {in_path} -> {out_path}")
        relabel_split(in_path, out_path, run_report)
    report_path = args.report or (output_dir / "relabel_report.json")
    write_report(run_report, report_path)
    print()
    print("=== Relabel report ===")
    for split_name, sr in run_report.splits.items():
        clean_pct = (
            (sr.afm_spans_already_clean + sr.afm_spans_relabelled)
            / sr.afm_spans_total
            if sr.afm_spans_total
            else 0.0
        )
        print(
            f"  {split_name}: records={sr.records_total} "
            f"afm_spans={sr.afm_spans_total} "
            f"already_clean={sr.afm_spans_already_clean} "
            f"relabelled={sr.afm_spans_relabelled} "
            f"unparseable={sr.afm_spans_unparseable} "
            f"clean_after={clean_pct * 100:.2f}%"
        )
    print(f"  full report: {report_path}")
    # Exit non-zero if any split has an unparseable rate above 1%, so
    # CI / launchers can gate on relabel quality.
    threshold = 0.01
    for sr in run_report.splits.values():
        if sr.afm_spans_total == 0:
            continue
        unparseable_rate = sr.afm_spans_unparseable / sr.afm_spans_total
        if unparseable_rate > threshold:
            print(
                f"FAIL: unparseable rate {unparseable_rate * 100:.2f}% "
                f"exceeds threshold {threshold * 100:.2f}%",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
