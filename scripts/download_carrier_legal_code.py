"""Download AI-team-UoA/greek_legal_code and emit clean carrier sentences.

The greek_legal_code dataset is ~47k Greek legal documents under
CC-BY-4.0 (Papaloukas et al. 2021, AI Team - University of Athens). The
model card requires attribution in derivative works; see LICENSING.md §2.

Output schema: one JSON object per line, `{"text": "<sentence>"}`.

Usage:

    pip install datasets
    python scripts/download_carrier_legal_code.py \
        --max-sentences 10000 \
        --output data/raw/greek_legal_sentences.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

_SENT_SPLIT = re.compile(r"(?<=[.!;·])\s+")
_WS = re.compile(r"\s+")


def _clean(s: str) -> str:
    return _WS.sub(" ", s).strip()


def _looks_usable(sentence: str) -> bool:
    if not sentence:
        return False
    if len(sentence) < 40 or len(sentence) > 260:
        return False
    if len(sentence.split()) < 6:
        return False
    if sentence[-1] not in ".!;·)":
        return False
    letters = [c for c in sentence if c.isalpha()]
    if not letters:
        return False
    greek = sum(1 for c in letters
                if "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿")
    if greek / len(letters) < 0.6:
        return False
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    p.add_argument("--max-sentences", type=int, default=10000)
    p.add_argument("--hf-split", default="train")
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

    ds = load_dataset(
        "AI-team-UoA/greek_legal_code", split=args.hf_split, streaming=True
    )

    n_written = 0
    with out.open("w", encoding="utf-8") as fp:
        for doc in ds:
            text = doc.get("text") or ""
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
    print(f"Wrote {n_written} legal carrier sentences to {out}")
    print("Attribution: Papaloukas et al. 2021, AI Team - University of Athens")
    print("License: CC-BY-4.0")


if __name__ == "__main__":
    main()
