"""Generate v2.12 Qwen phone-anchor pack.

Targets the v2.11 phone→account confusion (12 cases on benchmark):
mobile phones (^69\\d{8}$) get classified as account_number on real Greek
prose. Root cause: v2.6 base had 952 account_number records with 10-digit
values, ~7% of which match phone format.

Strategy: produce ~300 narrative records where a Greek mobile phone
appears DIRECTLY in a phone-context marker ("τηλέφωνο", "Κιν.", "καλέστε",
emoji 📞) while NO account-context word ("λογαριασμός") is nearby. Force
the model to anchor "phone marker + 69x..." → private_phone strongly.

Usage:
    python scripts/data_packs/generate_qwen_phone_anchor_pack.py \\
        --output data/processed/v2_12_phone_anchor_pack.jsonl \\
        --target-count 300 --batch-size 10 --seed 2032
"""
from __future__ import annotations

import argparse
import json
import random
import re
import string
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def gen_mobile_phone(rng: random.Random) -> str:
    return "69" + "".join(rng.choices(string.digits, k=8))


def gen_landline(rng: random.Random) -> str:
    prefix = rng.choice(["210", "211", "213", "231", "241", "251", "261", "271", "281"])
    return prefix + "".join(rng.choices(string.digits, k=10 - len(prefix)))


def gen_phone(rng: random.Random) -> str:
    return gen_mobile_phone(rng) if rng.random() < 0.7 else gen_landline(rng)


REGISTERS = [
    (
        "SMS με κινητό",
        "Σύντομο SMS 8-20 λέξεις με EXPLICIT marker «κιν.» ή «τηλ.» ή "
        "emoji 📞 ή «καλέστε» αμέσως πριν τον αριθμό. ΟΧΙ αναφορά σε "
        "λογαριασμό, χρέωση, μισθοδοσία, IBAN. Π.χ. «Κιν. πελάτη: [φωνη]».",
    ),
    (
        "ιατρική επικοινωνία",
        "Σύντομη ιατρική σημείωση 15-30 λέξεις με «τηλ. ασθενούς», "
        "«καλέστε στο», «επικοινωνία στο τηλέφωνο» κ.λπ. ΟΧΙ αναφορά σε "
        "λογαριασμούς ή χρεώσεις.",
    ),
    (
        "επιχειρηματική κάρτα",
        "Φράση που μοιάζει με contact info από επαγγελματική κάρτα — "
        "Email + τηλέφωνο. Π.χ. «τηλ.: 6912345678 / email: ...». ΟΧΙ "
        "αναφορά σε τραπεζικούς λογαριασμούς.",
    ),
    (
        "παράδοση δέματος",
        "Ειδοποίηση παράδοσης δέματος: παραλήπτης + τηλέφωνο "
        "επικοινωνίας. ΟΧΙ τραπεζικά στοιχεία.",
    ),
    (
        "support ticket",
        "Σύντομο μήνυμα προς τμήμα υποστήριξης 15-30 λέξεις, με "
        "«τηλέφωνο επικοινωνίας μου είναι» ή «καλέστε με στο». ΟΧΙ "
        "αναφορά σε «λογαριασμός», «μισθοδοσία», «χρέωση».",
    ),
]

_SYS = (
    "Είσαι παραγωγός ελληνικού κειμένου για NER training. "
    "Παράγεις φυσικές, σύντομες ελληνικές προτάσεις. "
    "ΟΧΙ σχόλια, ΟΧΙ σκέψεις."
)

_NUM_LINE_RE = re.compile(r"^\s*(\d{1,3})[\.\)]\s+(.*)$")


def build_prompt(register, register_desc, phones):
    lines = [f"{i+1}. τηλέφωνο: {p}" for i, p in enumerate(phones)]
    return (
        f"Ύφος: {register}.\n"
        f"Οδηγίες: {register_desc}\n\n"
        f"Γράψε ΑΚΡΙΒΩΣ {len(phones)} αριθμημένες προτάσεις (1., 2., …) "
        "που να περιέχουν αυτούσιο τον αριθμό τηλεφώνου.\n\n"
        f"Αριθμοί:\n" + "\n".join(lines) + "\n\n"
        "Κανόνες:\n"
        "- Ο αριθμός εμφανίζεται ΑΥΤΟΥΣΙΟΣ.\n"
        "- ΥΠΟΧΡΕΩΤΙΚΑ marker «τηλέφωνο» / «τηλ.» / «κιν.» / «καλέστε» / 📞 "
        "  μέσα στην ίδια πρόταση.\n"
        "- ΠΟΤΕ ΜΗ χρησιμοποιείς τις λέξεις «λογαριασμός», «μισθοδοσία», "
        "«χρέωση», «IBAN», «account» στην ίδια πρόταση.\n"
        "- 8-30 λέξεις ανά πρόταση.\n"
        "- Κάθε πρόταση σε ξεχωριστή γραμμή με αριθμό «1.», «2.», ..."
    )


def call_qwen(host, sys_prompt, user_prompt, temperature=0.8, max_tokens=1500):
    body = json.dumps({
        "model": "qwen",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"]


_BAD_WORDS_RE = re.compile(r"λογαριασμ|μισθοδοσ|IBAN|account|χρέωση", re.IGNORECASE)


def parse(content, phones, register_name):
    parsed = {}
    for line in content.splitlines():
        m = _NUM_LINE_RE.match(line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        text = m.group(2).strip()
        if 0 <= idx < len(phones) and text and idx not in parsed:
            parsed[idx] = text

    out = []
    for i, phone in enumerate(phones):
        text = parsed.get(i)
        if not text:
            continue
        # Reject if Qwen included account-context words despite instruction
        if _BAD_WORDS_RE.search(text):
            continue
        pos = text.find(phone)
        if pos < 0:
            continue
        out.append({
            "text": text,
            "label": [{"category": "private_phone",
                       "start": pos, "end": pos + len(phone)}],
            "info": {"source": "v2_12_phone_anchor",
                     "domain": f"register:{register_name}",
                     "strategy": "qwen3.6-35b-a3b/local"},
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--target-count", type=int, default=300)
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--seed", type=int, default=2032)
    ap.add_argument("--host", default="http://localhost:8080")
    ap.add_argument("--max-batches", type=int, default=80)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    batches = 0
    skipped = 0
    t0 = time.time()
    with args.output.open("w", encoding="utf-8") as f:
        while written < args.target_count and batches < args.max_batches:
            batches += 1
            register, register_desc = rng.choice(REGISTERS)
            phones = [gen_phone(rng) for _ in range(args.batch_size)]
            try:
                t_start = time.time()
                content = call_qwen(args.host, _SYS,
                                    build_prompt(register, register_desc, phones))
                tcall = time.time() - t_start
            except Exception as e:
                print(f"[batch {batches}] FAIL: {e}", flush=True)
                continue
            recs = parse(content, phones, register)
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            written += len(recs)
            skipped += args.batch_size - len(recs)
            print(f"[b{batches:>3} {tcall:5.1f}s] {register[:25]:<25} "
                  f"+{len(recs)}/{args.batch_size}  total={written}/{args.target_count}",
                  flush=True)
    print(f"\nDONE  {written} records / {batches} batches "
          f"({(time.time()-t0)/60:.1f} min, {skipped} skipped)")


if __name__ == "__main__":
    main()
