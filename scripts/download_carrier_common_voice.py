"""Download Mozilla Common Voice Greek text corpus and emit carrier sentences.

Common Voice text corpus is released under CC0 (public domain).
This script pulls only the TEXT corpus (not audio) — no ML-friendly
HuggingFace dataset is hosted by Mozilla for the text-only corpus, so we
fetch it directly from the Common Voice GitHub archive.

Output schema: one JSON object per line, `{"text": "<sentence>"}`.

Usage:

    python scripts/download_carrier_common_voice.py \
        --max-sentences 5000 \
        --output data/raw/common_voice_el_sentences.jsonl
"""
from __future__ import annotations

import argparse
import io
import json
import re
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Mozilla Common Voice maintains the validated sentence corpus per locale in
# the common-voice/common-voice GitHub repo under server/data/el/*.txt.
# Stable HTTPS URL for the aggregated sentence file:
COMMON_VOICE_EL_URL = (
    "https://raw.githubusercontent.com/common-voice/common-voice/"
    "main/server/data/el/sentence-collector.txt"
)

_WS = re.compile(r"\s+")


def _clean(s: str) -> str:
    return _WS.sub(" ", s).strip()


def _looks_usable(sentence: str) -> bool:
    if not sentence:
        return False
    if len(sentence) < 20 or len(sentence) > 180:
        return False
    if len(sentence.split()) < 4:
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
    p.add_argument("--max-sentences", type=int, default=5000)
    p.add_argument("--url", default=COMMON_VOICE_EL_URL)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {args.url} ...")
    with urllib.request.urlopen(args.url, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")

    n_written = 0
    with out.open("w", encoding="utf-8") as fp:
        for line in raw.splitlines():
            s = _clean(line)
            if _looks_usable(s):
                fp.write(json.dumps({"text": s}, ensure_ascii=False) + "\n")
                n_written += 1
                if n_written >= args.max_sentences:
                    break
    print(f"Wrote {n_written} Common Voice EL carrier sentences to {out}")
    print("License: CC0 (public domain)")


if __name__ == "__main__":
    main()
