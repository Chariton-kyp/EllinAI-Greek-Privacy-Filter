"""Run trained teacher over Greek corpus → pseudo-labels for distillation.

Two transport modes:

  --engine local-vllm        load LoRA adapter + base in-process via vLLM
                             (fastest on Linux GPU, requires vllm install)

  --engine openai-server     hit any OpenAI-compatible endpoint serving the
                             teacher (e.g. local llama.cpp Docker, vLLM,
                             SGLang, AWS endpoint). Default: localhost:8080.

Output JSONL has the SAME schema as v2.X gold data so the distillation
trainer can mix gold + pseudo without conversion:

    {"text": "<text>",
     "label": [{"category": "afm", "start": 5, "end": 14}, ...],
     "info": {"source": "v3_pseudo", "teacher": "<hf-id>", "confidence": <int>}}

The teacher's JSON-spans output is parsed and resolved to char offsets
via verbatim substring search. Records where any span fails to locate
are dropped (high-confidence-only).

Usage (local OpenAI-compatible endpoint, e.g. llama.cpp Docker):
    python scripts/v3/generate_pseudo_labels.py \\
        --engine openai-server \\
        --host http://127.0.0.1:8080 \\
        --teacher-id "google/gemma-4-31B-it" \\
        --input data/processed/v3_corpus/greek_corpus.jsonl \\
        --output data/processed/v3_pseudo/pseudo_labels.jsonl \\
        --batch-size 8 --max-records 500000
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path


SYSTEM_PROMPT = (
    "Είσαι σύστημα ανίχνευσης ευαίσθητων προσωπικών δεδομένων (PII) σε "
    "ελληνικό κείμενο. Όταν σου δίνεται ένα κείμενο, απαντάς ΑΠΟΚΛΕΙΣΤΙΚΑ "
    "με μια έγκυρη JSON λίστα από αντικείμενα της μορφής:\n"
    "  [{\"label\": \"<class>\", \"value\": \"<αυτούσιο απόσπασμα>\"}, ...]\n"
    "Αν δεν υπάρχει κανένα PII, απάντησε []. ΟΧΙ σχόλια, ΟΧΙ markdown."
)

_JSON_LIST_RE = re.compile(r"\[\s*(?:\{.*?\})?\s*(?:,\s*\{.*?\}\s*)*\]", re.DOTALL)


def call_openai(host: str, model: str, user_prompt: str,
                  max_tokens: int, temperature: float) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"]


def parse_spans(content: str) -> list[dict] | None:
    """Extract first valid JSON-list-of-spans from the model output."""
    content = content.strip()
    # Try direct parse first
    try:
        v = json.loads(content)
        if isinstance(v, list):
            return v
    except json.JSONDecodeError:
        pass
    # Fallback: find first JSON array via regex
    m = _JSON_LIST_RE.search(content)
    if not m:
        return None
    try:
        v = json.loads(m.group(0))
        return v if isinstance(v, list) else None
    except json.JSONDecodeError:
        return None


def resolve_offsets(text: str, spans: list[dict]) -> list[dict] | None:
    """Convert {label,value} → {category,start,end} via verbatim find.

    Strict mode: cursor advances after each match so duplicate values don't
    collapse to the same offset. If any span fails to resolve (cursor-only,
    no fallback to text.find with cursor=0), the WHOLE record returns None
    so the caller drops it — keeps span data clean.
    (Reviewer I-1: previous version had cursor-bypass fallback that
    silently produced duplicate offsets on repeated PII values.)
    """
    out = []
    cursor = 0
    for s in spans:
        if not isinstance(s, dict):
            return None
        lbl = s.get("label")
        val = s.get("value")
        if not lbl or not val:
            return None
        idx = text.find(val, cursor)
        if idx < 0:
            return None  # cannot resolve at-or-after cursor → drop whole record
        out.append({
            "category": lbl,
            "start": idx,
            "end": idx + len(val),
        })
        cursor = idx + len(val)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--engine", choices=["openai-server"], default="openai-server")
    p.add_argument("--host", default="http://127.0.0.1:8080")
    p.add_argument("--teacher-id", required=True,
                    help="HF id (just for provenance metadata).")
    p.add_argument("--model", default="qwen",
                    help="Server-side model alias.")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-records", type=int, default=None)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--resume", action="store_true",
                    help="Skip records already present in output (by text hash).")
    args = p.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    seen_hashes: set[int] = set()
    if args.resume and args.output.exists():
        with args.output.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    seen_hashes.add(hash(rec["text"]))
                except (json.JSONDecodeError, KeyError):
                    continue
        print(f"[resume] skipping {len(seen_hashes)} already-labelled records",
              flush=True)

    written = 0
    skipped_parse = 0
    skipped_offsets = 0
    t_start = time.time()

    mode = "a" if args.resume else "w"
    with args.input.open(encoding="utf-8") as fin, \
         args.output.open(mode, encoding="utf-8") as fout:
        for n, line in enumerate(fin):
            if args.max_records and written >= args.max_records:
                break
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            text = rec.get("text", "")
            if not text:
                continue
            if args.resume and hash(text) in seen_hashes:
                continue

            try:
                t0 = time.time()
                content = call_openai(args.host, args.model, text,
                                       args.max_tokens, args.temperature)
                tcall = time.time() - t0
            except Exception as e:
                print(f"[record {n}] CALL FAILED: {e}", flush=True)
                continue

            spans = parse_spans(content)
            if spans is None:
                skipped_parse += 1
                continue

            resolved = resolve_offsets(text, spans)
            if resolved is None:
                # Any span unresolvable at-or-after cursor → drop record
                # to avoid teaching student bad boundaries.
                skipped_offsets += 1
                continue

            out_rec = {
                "text": text,
                "label": resolved,
                "info": {
                    "source": "v3_pseudo",
                    "teacher": args.teacher_id,
                    "src_corpus": rec.get("info", {}).get("source", "unknown"),
                    "src_license": rec.get("info", {}).get("license", "unknown"),
                },
            }
            fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
            fout.flush()
            written += 1
            if written % 50 == 0:
                rate = written / (time.time() - t_start)
                print(f"[{written:>6}] +{tcall:5.1f}s rate={rate*60:.1f}/min "
                      f"parse_drop={skipped_parse} offset_drop={skipped_offsets}",
                      flush=True)

    elapsed = time.time() - t_start
    print(f"\nDONE  written={written} parse_drop={skipped_parse} "
          f"offset_drop={skipped_offsets} elapsed={elapsed/60:.1f}min")


if __name__ == "__main__":
    main()
