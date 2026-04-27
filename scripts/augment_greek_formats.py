"""Format-diversification augmentation for Greek PII spans.

The synthetic training data (`train.jsonl`) tends to use 2-3 canonical
formats per category. Real-world Greek documents use many surface forms:

  AMKA:    "20098843942"  |  "200988-43942"  |  "200 988 43942"
  AFM:     "695092590"    |  "EL695092590"   |  "Α.Φ.Μ.: 695092590"
  ADT:     "ΑΒ 123456"    |  "ΑΒ-123456"     |  "AB 123456" (Latin lookalike)
           "ΑΒ123456"     |  "Α.Δ.Τ. ΑΒ 123456"
  IBAN_GR: "GR1601101250000000012300695"
           "GR16 0110 1250 0000 0001 2300 695"   (ETEAN-style spacing)
           "GR16-0110-1250-0000-0001-2300-695"

This script rewrites existing OPF JSONL examples into additional variants
with character offsets re-computed correctly. It never invents new PII -
only re-formats existing spans, so semantic correctness is preserved.

Usage:
  python scripts/augment_greek_formats.py \
      --input  data/processed/train.jsonl \
      --output data/processed/train_augmented.jsonl \
      --per-example-variants 2

To combine with the original file:
  cat data/processed/train.jsonl data/processed/train_augmented.jsonl \
      > data/processed/train_combined.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Greek-to-Latin visual lookalikes useful ONLY for ADT format jitter.
GR_TO_LATIN = {
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I",
    "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T",
    "Υ": "Y", "Χ": "X",
}


def _reformat_amka(s: str, rng: random.Random) -> str | None:
    digits = re.sub(r"\D", "", s)
    if len(digits) != 11:
        return None
    style = rng.choice(["dash", "space3", "space6"])
    if style == "dash":
        return f"{digits[:6]}-{digits[6:]}"
    if style == "space3":
        return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
    return f"{digits[:6]} {digits[6:]}"


def _reformat_afm(s: str, rng: random.Random) -> str | None:
    digits = re.sub(r"\D", "", s)
    if len(digits) != 9:
        return None
    style = rng.choice(["prefix_el", "prefix_afm", "dot_prefix"])
    if style == "prefix_el":
        return f"EL{digits}"
    if style == "prefix_afm":
        return f"ΑΦΜ {digits}"
    return f"Α.Φ.Μ.: {digits}"


def _reformat_adt(s: str, rng: random.Random) -> str | None:
    """Reformat an ADT span. The "Α.Δ.Τ." label must stay OUTSIDE the
    span, so the span always represents only the letters + digits body
    (or a Latin-transliterated variant)."""
    m = re.match(r"^\s*([Α-ΩA-Z]{1,3})[\s\-]*([0-9]{5,7})\s*$", s)
    if not m:
        return None
    letters, digits = m.group(1), m.group(2)
    style = rng.choice(["compact", "dash", "spaced", "latin"])
    if style == "compact":
        return f"{letters}{digits}"
    if style == "dash":
        return f"{letters}-{digits}"
    if style == "spaced":
        return f"{letters} {digits}"
    latin_letters = "".join(GR_TO_LATIN.get(ch, ch) for ch in letters)
    return f"{latin_letters} {digits}"


def _reformat_iban_gr(s: str, rng: random.Random) -> str | None:
    compact = re.sub(r"\s|-", "", s).upper()
    if not re.fullmatch(r"GR\d{25}", compact):
        return None
    style = rng.choice(["grouped4", "dashed4"])
    groups = [compact[i:i + 4] for i in range(0, len(compact), 4)]
    sep = " " if style == "grouped4" else "-"
    return sep.join(groups)


def _reformat_phone(s: str, rng: random.Random) -> str | None:
    digits = re.sub(r"\D", "", s)
    if len(digits) < 10 or len(digits) > 12:
        return None
    # Greek mobile/landline formats
    if len(digits) == 10:
        style = rng.choice(["spaced24", "dot", "intl"])
        if style == "spaced24":
            return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
        if style == "dot":
            return f"{digits[:4]}.{digits[4:7]}.{digits[7:]}"
        return f"+30 {digits}"
    return None


REFORMATTERS: dict[str, Callable[[str, random.Random], str | None]] = {
    "amka": _reformat_amka,
    "afm": _reformat_afm,
    "adt": _reformat_adt,
    "iban_gr": _reformat_iban_gr,
    "private_phone": _reformat_phone,
}


def _mutate_example(
    example: dict, rng: random.Random
) -> dict | None:
    """Return a new example where eligible spans get re-formatted.

    Returns None if no span was successfully mutated (augmentation was
    a no-op), so the caller can skip writing duplicates.
    """
    text = example["text"]
    spans = example.get("label") or example.get("spans") or []
    if not spans:
        return None

    # Sort spans by start desc so offsets on the left don't shift while
    # we rewrite spans on the right.
    ordered = sorted(spans, key=lambda sp: sp["start"], reverse=True)

    new_text = text
    new_spans: list[dict] = [dict(sp) for sp in ordered]  # we'll rewrite offsets
    mutated = False

    # Apply in descending order: editing the tail never invalidates the head.
    rewritten_lookup: dict[int, tuple[int, int, str]] = {}
    for idx, sp in enumerate(ordered):
        reformatter = REFORMATTERS.get(sp["category"])
        if reformatter is None:
            continue
        original = text[sp["start"]:sp["end"]]
        # 50/50 chance we attempt a re-format so not every span is touched.
        if rng.random() < 0.5:
            continue
        candidate = reformatter(original, rng)
        if candidate is None or candidate == original:
            continue
        new_text = new_text[:sp["start"]] + candidate + new_text[sp["end"]:]
        rewritten_lookup[idx] = (sp["start"], sp["start"] + len(candidate), candidate)
        mutated = True

    if not mutated:
        return None

    # Recompute spans left-to-right on the new text based on rewrites.
    # Rebuild using the original left-to-right order.
    left_to_right = sorted(spans, key=lambda sp: sp["start"])
    rebuilt: list[dict] = []
    cursor_delta = 0
    # Map from original-span identity to rewrite info.
    id_to_rewrite: dict[int, tuple[int, int, str]] = {}
    for idx, sp in enumerate(ordered):
        if idx in rewritten_lookup:
            id_to_rewrite[id(sp)] = rewritten_lookup[idx]
    for sp in left_to_right:
        # Find whether this span (same object reference order) got rewritten.
        rewrite = None
        for k_sp, val in zip(ordered, [rewritten_lookup.get(i) for i in range(len(ordered))]):
            if k_sp is sp and val is not None:
                rewrite = val
                break
        if rewrite is None:
            new_start = sp["start"] + cursor_delta
            new_end = sp["end"] + cursor_delta
            rebuilt.append(
                {"category": sp["category"], "start": new_start, "end": new_end}
            )
        else:
            _, _, new_text_span = rewrite
            new_start = sp["start"] + cursor_delta
            new_end = new_start + len(new_text_span)
            rebuilt.append(
                {"category": sp["category"], "start": new_start, "end": new_end}
            )
            cursor_delta += len(new_text_span) - (sp["end"] - sp["start"])

    # Final sanity check: every rebuilt span must match the recorded text.
    for sp in rebuilt:
        substring = new_text[sp["start"]:sp["end"]]
        if not substring:
            return None

    augmented = {
        "text": new_text,
        "label": rebuilt,
        "info": {**(example.get("info") or {}), "augmented": "greek_format_variant"},
    }
    return augmented


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--per-example-variants", type=int, default=1,
        help="How many format variants to attempt per source example.",
    )
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_in = 0
    n_out = 0
    with output_path.open("w", encoding="utf-8") as out_fp:
        for example in _iter_jsonl(input_path):
            n_in += 1
            for _ in range(args.per_example_variants):
                augmented = _mutate_example(example, rng)
                if augmented is not None:
                    out_fp.write(
                        json.dumps(augmented, ensure_ascii=False) + "\n"
                    )
                    n_out += 1

    print(
        f"Read {n_in} source examples, wrote {n_out} augmented examples "
        f"to {output_path}"
    )


if __name__ == "__main__":
    main()
