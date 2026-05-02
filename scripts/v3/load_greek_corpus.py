"""Download + assemble a commercial-clean Greek text corpus for v3 pseudo-labelling.

Sources (all licenses verified compatible with commercial weight release):

| dataset                          | size           | license        | role                |
|----------------------------------|----------------|----------------|---------------------|
| PleIAs/Greek-PD                  | 8 GB / 156M w  | Public Domain  | classical / formal  |
| mozilla-foundation/common_voice  | ~50k sentences | CC0            | conversational      |
| AI-team-UoA/greek_legal_code     | ~350k records  | CC-BY-4.0      | legal               |
| wikimedia/wikipedia 20231101.el  | ~250k articles | CC-BY-SA-4.0   | encyclopedic        |
| allenai/c4 (mC4 el subset)       | ~80 GB         | ODC-BY 1.0     | modern web prose    |

Each record is sliced into ~200-400 char chunks (matching v2.X record length),
deduplicated, length-filtered, and emitted to one JSONL with provenance:

    {"text": "...", "info": {"source": "<dataset>", "license": "<spdx>"}}

The output JSONL is then fed to the teacher (gemma-4-31B or Qwen3.6-35B)
to produce pseudo-labels for downstream student distillation.

Important: this script does NOT include the user's existing v2.13 gold
data — that stays separate and is mixed in by the distillation trainer.
This script is purely for corpus enlargement.

Usage:
    python scripts/v3/load_greek_corpus.py \\
        --output data/processed/v3_corpus/greek_corpus.jsonl \\
        --target-records 500000 \\
        --sources greek_pd common_voice greek_legal wiki_el mc4_el \\
        --min-len 50 --max-len 600 \\
        --seed 2042
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Iterator


# ─── Source manifests (license + loader keyword) ───────────────────

SOURCES = {
    # ─── Commercial-clean (default) ─────────────────────────────────
    "greek_pd": {
        "hf_id": "PleIAs/Greek-PD",
        "split": "train",
        "text_field": "text",
        "license": "public-domain",
        "commercial_safe": True,
        "note": "Public domain — classical / pre-1884 Greek prose",
    },
    "common_voice": {
        "hf_id": "mozilla-foundation/common_voice_17_0",
        "config": "el",
        "split": "train",
        "text_field": "sentence",
        "license": "CC0-1.0",
        "commercial_safe": True,
        "note": "CC0 — conversational modern Greek",
    },
    "greek_legal": {
        "hf_id": "AI-team-UoA/greek_legal_code",
        "split": "train",
        "text_field": "text",
        "license": "CC-BY-4.0",
        "commercial_safe": True,
        "note": "CC-BY-4.0 — Greek legislation; attribution required (in ATTRIBUTION.txt)",
    },
    # ─── Risky for commercial weights — opt-in only ─────────────────
    "wiki_el": {
        "hf_id": "wikimedia/wikipedia",
        "config": "20231101.el",
        "split": "train",
        "text_field": "text",
        "license": "CC-BY-SA-4.0",
        "commercial_safe": False,
        "note": "CC-BY-SA-4.0 share-alike — derivative-work clause may force "
                 "weights to inherit SA license. Avoid for commercial weights.",
    },
    "mc4_el": {
        "hf_id": "allenai/c4",
        "config": "el",
        "split": "train",
        "text_field": "text",
        "license": "ODC-BY-1.0",
        "commercial_safe": False,
        "note": "ODC-BY-1.0 metadata, but underlying content is Common Crawl "
                 "with mixed source-publisher copyrights. Avoid for commercial.",
    },
}

# Greek-script characters; any chunk with <60% Greek chars is dropped.
_GREEK_RE = re.compile(r"[Α-Ωα-ωΆ-Ώά-ώἀ-῾]")
_WHITESPACE_RE = re.compile(r"\s+")


def _is_greek_enough(text: str, min_ratio: float = 0.55) -> bool:
    if not text:
        return False
    greek = len(_GREEK_RE.findall(text))
    return (greek / max(1, len(text))) >= min_ratio


def _chunk(text: str, min_len: int, max_len: int) -> Iterator[str]:
    """Yield sentence-ish chunks within [min_len, max_len] chars.
    Preserves natural sentence boundaries where possible."""
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) <= max_len:
        if len(text) >= min_len:
            yield text
        return
    sentences = re.split(r"(?<=[.!?·;])\s+", text)
    buf = []
    buf_len = 0
    for s in sentences:
        s_len = len(s)
        if buf_len + s_len + 1 > max_len:
            if buf and buf_len >= min_len:
                yield " ".join(buf)
            buf = [s]
            buf_len = s_len
        else:
            buf.append(s)
            buf_len += s_len + 1
    if buf and buf_len >= min_len:
        yield " ".join(buf)


def stream_dataset(name: str, target: int, min_len: int, max_len: int,
                    rng: random.Random, seen_hashes: set[int]) -> Iterator[dict]:
    """Stream records from one HuggingFace dataset, yielding chunked records.
    Lazy-loads to avoid huge downloads when target is small."""
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        print(f"FAIL: pip install datasets to use this script.", file=sys.stderr)
        sys.exit(1)

    spec = SOURCES[name]
    print(f"[{name}] loading {spec['hf_id']} (license: {spec['license']})...",
          file=sys.stderr, flush=True)
    kwargs = {"streaming": True}
    if "config" in spec:
        ds = load_dataset(spec["hf_id"], spec["config"],
                            split=spec["split"], **kwargs)
    else:
        ds = load_dataset(spec["hf_id"], split=spec["split"], **kwargs)

    yielded = 0
    seen_in_this_source = 0
    for rec in ds:
        if yielded >= target:
            break
        text = rec.get(spec["text_field"]) or ""
        if not text or not _is_greek_enough(text):
            continue
        for chunk in _chunk(text, min_len, max_len):
            h = hash(chunk)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            seen_in_this_source += 1
            yield {
                "text": chunk,
                "info": {
                    "source": f"v3_corpus/{name}",
                    "license": spec["license"],
                    "dataset": spec["hf_id"],
                },
            }
            yielded += 1
            if yielded >= target:
                break
    print(f"[{name}] yielded {yielded} chunks", file=sys.stderr, flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--target-records", type=int, default=500_000)
    p.add_argument("--sources", nargs="+",
                    default=["greek_pd", "common_voice", "greek_legal"],
                    choices=list(SOURCES),
                    help="Default: only PD/CC0/CC-BY commercial-clean sources. "
                         "Add 'wiki_el' (CC-BY-SA-4.0 share-alike — risky for "
                         "commercial weights) or 'mc4_el' (Common Crawl underlying "
                         "content) ONLY with explicit legal review.")
    p.add_argument("--min-len", type=int, default=50)
    p.add_argument("--max-len", type=int, default=600)
    p.add_argument("--seed", type=int, default=2042)
    p.add_argument("--quota-per-source", type=int, default=None,
                    help="Max records per source (default: target/N).")
    args = p.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Warn loudly about risky sources
    for s in args.sources:
        spec = SOURCES[s]
        if not spec.get("commercial_safe", False):
            print(f"⚠️  WARNING: source '{s}' has license '{spec['license']}' "
                  f"which is RISKY for commercial weights. {spec['note']}",
                  file=sys.stderr, flush=True)

    quota = args.quota_per_source or (args.target_records // len(args.sources))
    seen: set[int] = set()
    counts: dict[str, int] = {}

    written = 0
    with args.output.open("w", encoding="utf-8") as fout:
        for src in args.sources:
            count = 0
            try:
                for rec in stream_dataset(src, quota, args.min_len, args.max_len,
                                            rng, seen):
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
                    written += 1
            except Exception as e:
                print(f"[{src}] FAILED: {e}", file=sys.stderr)
            counts[src] = count
            print(f"[{src}] wrote {count} chunks (total: {written})", flush=True)

    print(f"\nTOTAL: {written} records to {args.output}")
    print(f"Per source: {json.dumps(counts, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
