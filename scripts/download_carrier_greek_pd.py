"""Download a slice of PleIAs/Greek-PD and emit clean carrier sentences.

Greek-PD is 156M words of pre-1884 public-domain Greek prose, published
by PleIAs. We only need a sentence-level carrier sample, not the full
~8 GB corpus, so this script streams the dataset and writes the first
`--max-sentences` clean sentences to a JSONL file.

Output schema: one JSON object per line, `{"text": "<sentence>"}`.

Usage:

    pip install datasets
    python scripts/download_carrier_greek_pd.py \
        --max-sentences 20000 \
        --output data/raw/greek_pd_sentences.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


_SENT_SPLIT = re.compile(r"(?<=[.!;·])\s+")
_WS = re.compile(r"\s+")


def _clean(sentence: str) -> str:
    return _WS.sub(" ", sentence).strip()


def _looks_usable(sentence: str) -> bool:
    if not sentence:
        return False
    if len(sentence) < 40 or len(sentence) > 220:
        return False
    # Discard OCR garbage: must have at least 6 words and a final punctuation.
    if len(sentence.split()) < 6:
        return False
    if sentence[-1] not in ".!;·":
        return False
    letters = [c for c in sentence if c.isalpha()]
    if not letters:
        return False
    greek = sum(1 for c in letters
                if "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿")
    if greek / len(letters) < 0.7:
        return False
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    p.add_argument("--max-sentences", type=int, default=20000)
    p.add_argument("--hf-split", default="train")
    p.add_argument(
        "--max-docs", type=int, default=500,
        help="Stop after processing this many source books (each book has "
             "hundreds of sentences).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "datasets package missing; run: pip install datasets"
        ) from exc

    ds = load_dataset("PleIAs/Greek-PD", split=args.hf_split, streaming=True)

    n_written = 0
    n_docs = 0
    with out.open("w", encoding="utf-8") as fp:
        for doc in ds:
            n_docs += 1
            if n_docs > args.max_docs:
                break
            text = doc.get("text") or doc.get("content") or ""
            if not text:
                continue
            for raw in _SENT_SPLIT.split(text):
                s = _clean(raw)
                if _looks_usable(s):
                    fp.write(json.dumps({"text": s}, ensure_ascii=False) + "\n")
                    n_written += 1
                    if n_written >= args.max_sentences:
                        break
            if n_written >= args.max_sentences:
                break
    print(f"Wrote {n_written} carrier sentences from {n_docs} docs to {out}")


if __name__ == "__main__":
    main()
