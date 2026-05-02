"""Convert v2.X OPF JSONL records to Unsloth-compatible chat-format SFT data.

Takes OPF span-labelled records and emits one JSONL per split where each
line is a chat-style message list:

    {
      "messages": [
        {"role": "system",    "content": "<system prompt>"},
        {"role": "user",      "content": "<Greek text>"},
        {"role": "assistant", "content": "<JSON spans>"}
      ]
    }

The assistant target is a strict JSON list of {label, value} pairs:

    [{"label":"afm","value":"123456789"},{"label":"private_person","value":"Ηλίας Σταματόπουλος"}]

Empty-label records emit `[]` so the model learns to predict no-PII when
no PII is present (without collapsing to "always empty" because we
balance against positive examples downstream).

This format is:
  * compact (1-3 tokens per span vs offset-based formats)
  * unambiguous (label + verbatim value)
  * easy to parse for span-F1 reward (during GRPO RL)
  * compatible with Unsloth's `apply_chat_template` for any of:
      gemma-4-*, qwen3-*, llama-3.*, mistral-*

Usage:
    python scripts/v3/convert_opf_to_chat.py \\
        --input  data/processed/v2_13_combined/train.jsonl \\
        --output data/processed/v3_chat/train.jsonl \\
        --label-space configs/label_space_v2.json \\
        --max-spans-per-record 12 \\
        --shuffle-spans \\
        --dropout-empty-rate 0.0
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path


SYSTEM_PROMPT_GREEK = (
    "Είσαι σύστημα ανίχνευσης ευαίσθητων προσωπικών δεδομένων (PII) σε "
    "ελληνικό κείμενο. Όταν σου δίνεται ένα κείμενο, απαντάς ΑΠΟΚΛΕΙΣΤΙΚΑ "
    "με μια έγκυρη JSON λίστα από αντικείμενα της μορφής:\n"
    "  [{{\"label\": \"<class>\", \"value\": \"<αυτούσιο απόσπασμα>\"}}, ...]\n\n"
    "Κάθε αντικείμενο αντιστοιχεί σε ένα PII span που εντόπισες. Το "
    "πεδίο `value` πρέπει να περιέχει ΑΥΤΟΥΣΙΑ τα ίδια κενά, διαλυτικά, "
    "παύλες και τόνους όπως εμφανίζονται στο κείμενο εισόδου. Αν δεν "
    "υπάρχει κανένα PII, απάντησε []. ΟΧΙ σχόλια, ΟΧΙ markdown, ΟΧΙ "
    "πρόσθετο κείμενο πριν ή μετά τη JSON λίστα.\n\n"
    "Έγκυρες κλάσεις: {label_list}"
)


def load_label_space(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        for key in ("classes", "span_class_names", "labels"):
            if key in data and isinstance(data[key], list):
                names = [c for c in data[key] if c and c != "O"]
                return sorted(names)
    if isinstance(data, list):
        return sorted([c for c in data if c and c != "O"])
    raise ValueError(f"Unrecognised label-space format at {path}")


def build_assistant_target(rec: dict, max_spans: int, shuffle: bool,
                            rng: random.Random) -> str:
    spans = []
    for lbl in rec.get("label", []) or []:
        cat = lbl.get("category")
        s, e = lbl.get("start"), lbl.get("end")
        if cat is None or s is None or e is None:
            continue
        value = rec["text"][s:e]
        if not value:
            continue
        spans.append({"label": cat, "value": value})

    # Shuffle FIRST so truncation drops a random subset, not always tail spans.
    # Otherwise rare classes appearing at end of long records (e.g. vehicle_vin
    # at record tail) are systematically excluded from training. (Reviewer I-5.)
    if shuffle and len(spans) > 1:
        spans = spans.copy()
        rng.shuffle(spans)

    if max_spans and len(spans) > max_spans:
        spans = spans[:max_spans]

    return json.dumps(spans, ensure_ascii=False, separators=(",", ":"))


def convert_record(rec: dict, label_list: list[str], max_spans: int,
                    shuffle: bool, rng: random.Random) -> dict:
    text = rec["text"]
    assistant = build_assistant_target(rec, max_spans, shuffle, rng)
    sys_prompt = SYSTEM_PROMPT_GREEK.format(label_list=", ".join(label_list))
    return {
        "messages": [
            {"role": "system",    "content": sys_prompt},
            {"role": "user",      "content": text},
            {"role": "assistant", "content": assistant},
        ]
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input", type=Path, required=True,
                    help="Input OPF JSONL file (v2.X format).")
    p.add_argument("--output", type=Path, required=True,
                    help="Output chat-format JSONL file.")
    p.add_argument("--label-space", type=Path,
                    default=Path("configs/label_space_v2.json"),
                    help="Label space JSON file (24 classes).")
    p.add_argument("--max-spans-per-record", type=int, default=20,
                    help="Truncate records with too many spans (rare).")
    p.add_argument("--shuffle-spans", action="store_true",
                    help="Shuffle span order in assistant target so model "
                         "doesn't memorise input order.")
    p.add_argument("--dropout-empty-rate", type=float, default=0.0,
                    help="Drop this fraction of empty-label records (helps "
                         "reduce 'predict O' bias if base data is imbalanced).")
    p.add_argument("--seed", type=int, default=2042)
    args = p.parse_args()

    rng = random.Random(args.seed)
    label_list = load_label_space(args.label_space)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped_empty_dropout = 0
    skipped_invalid = 0
    span_count = Counter()
    empty_records = 0

    with args.input.open(encoding="utf-8") as fin, args.output.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped_invalid += 1
                continue
            if "text" not in rec:
                skipped_invalid += 1
                continue

            labels = rec.get("label", []) or []
            if not labels:
                empty_records += 1
                if args.dropout_empty_rate > 0 and rng.random() < args.dropout_empty_rate:
                    skipped_empty_dropout += 1
                    continue

            chat = convert_record(rec, label_list,
                                   args.max_spans_per_record,
                                   args.shuffle_spans, rng)
            fout.write(json.dumps(chat, ensure_ascii=False) + "\n")
            written += 1
            for lbl in labels:
                cat = lbl.get("category")
                if cat:
                    span_count[cat] += 1

    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"  written:                {written}")
    print(f"  empty-label records:    {empty_records}")
    print(f"  empty dropped (dropout): {skipped_empty_dropout}")
    print(f"  invalid skipped:        {skipped_invalid}")
    print(f"  total span occurrences: {sum(span_count.values())}")
    print(f"  classes seen ({len(span_count)}): "
          f"{sorted(span_count.items(), key=lambda kv: -kv[1])[:5]}...")


if __name__ == "__main__":
    main()
