"""Generate local-Qwen contrastive v2.13 records.

This script intentionally does not call OpenAI services. It sends
deterministic, fictional slot values to a local Ollama or OpenAI-
compatible endpoint such as llama-server serving an Apache-compatible
Qwen GGUF.

The generated record text comes from the local model. Span labels are
created only when every slot value is found verbatim in the returned
sentence.
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from generate_commercial_safe_greek_pii import (  # noqa: E402
    gen_account_number,
    gen_afm,
    gen_email,
    gen_person,
    gen_phone,
    gen_secret,
)
from generate_tier1_records import (  # noqa: E402
    gen_ama,
    gen_imei,
    gen_ip_address,
    gen_mac_address,
    gen_vehicle_vin,
)


NUM_LINE_RE = re.compile(r"^\s*(\d{1,3})[\.\)]\s+(.*)$")

SYSTEM_PROMPT = (
    "Είσαι παραγωγός ελληνικού κειμένου για NER training. "
    "Χρησιμοποιείς μόνο τις δοσμένες τιμές, αυτούσιες. "
    "Δεν γράφεις εξηγήσεις, σχόλια ή markdown."
)

LABEL_DISPLAY = {
    "account_number": "αριθμός λογαριασμού",
    "afm": "ΑΦΜ",
    "ama": "ΑΜΑ ΙΚΑ",
    "amka": "ΑΜΚΑ",
    "driver_license": "αριθμός διπλώματος",
    "imei": "IMEI",
    "ip_address": "διεύθυνση IP",
    "mac_address": "διεύθυνση MAC",
    "private_email": "email επικοινωνίας",
    "private_person": "ονοματεπώνυμο",
    "private_phone": "τηλέφωνο επικοινωνίας",
    "secret": "κλειδί API ή token",
    "vehicle_vin": "VIN/αριθμός πλαισίου",
}


def gen_amka(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=11))


def gen_driver_license_value(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=9))


PACKS = {
    "phone_account": {
        "description": (
            "Σύντομα φυσικά ελληνικά μηνύματα όπου υπάρχει τηλέφωνο επικοινωνίας "
            "και ξεχωριστός αριθμός λογαριασμού. Το τοπικό συμφραζόμενο πρέπει "
            "να κάνει καθαρό ποιο είναι τηλέφωνο και ποιο λογαριασμός."
        ),
        "slots": [
            ("private_phone", gen_phone),
            ("account_number", gen_account_number),
        ],
    },
    "mac_ip_vin": {
        "description": (
            "Τεχνικά logs ή δελτία συνεργείου με διεύθυνση MAC, διεύθυνση IP "
            "και αριθμό πλαισίου οχήματος (VIN). Φυσικά ελληνικά. ΑΠΑΓΟΡΕΥΕΤΑΙ "
            "να γράψεις τα label IDs «mac_address», «ip_address», «vehicle_vin» "
            "αυτούσια — πες «διεύθυνση MAC», «IP», «αριθμός πλαισίου» ή «VIN»."
        ),
        "slots": [
            ("mac_address", gen_mac_address),
            ("ip_address", gen_ip_address),
            ("vehicle_vin", gen_vehicle_vin),
        ],
    },
    "email_secret": {
        "description": (
            "Μηνύματα τεχνικής υποστήριξης ή περιστατικά ασφαλείας όπου υπάρχει "
            "κανονικό email επικοινωνίας και ξεχωριστό κλειδί API / token. "
            "Φυσικά ελληνικά. ΜΗΝ χρησιμοποιείς τη λέξη «secret» αυτούσια στο "
            "κείμενο — πες «κλειδί API», «token πρόσβασης», «κωδικός υπηρεσίας»."
        ),
        "slots": [
            ("private_email", gen_email),
            ("secret", gen_secret),
        ],
    },
    "person_admin_dense": {
        "description": (
            "Φυσικά ελληνικά διοικητικά κείμενα με ονοματεπώνυμο, ΑΜΚΑ, ΑΦΜ, "
            "ΑΜΑ ΙΚΑ και αριθμό διπλώματος. Να μοιάζει με επιστολή, αίτηση ή "
            "σημείωση υπηρεσίας, όχι με λίστα πεδίων."
        ),
        "slots": [
            ("private_person", gen_person),
            ("amka", gen_amka),
            ("afm", gen_afm),
            ("ama", gen_ama),
            ("driver_license", gen_driver_license_value),
        ],
    },
    "imei_phone": {
        "description": (
            "Σημειώσεις κινητής συσκευής ή ασφαλιστικής δήλωσης όπου υπάρχει "
            "IMEI και τηλέφωνο επικοινωνίας στο ίδιο κείμενο με σαφείς δείκτες."
        ),
        "slots": [
            ("imei", gen_imei),
            ("private_phone", gen_phone),
        ],
    },
}


def call_openai_compatible(host: str, model: str, user_prompt: str, max_tokens: int) -> str:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.75,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def call_ollama(host: str, model: str, user_prompt: str, max_tokens: int) -> str:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.75,
                "num_predict": max_tokens,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["message"]["content"]


def call_local_model(
    engine: str,
    host: str,
    model: str,
    user_prompt: str,
    max_tokens: int,
) -> str:
    if engine == "ollama":
        return call_ollama(host, model, user_prompt, max_tokens)
    return call_openai_compatible(host, model, user_prompt, max_tokens)


def make_items(pack: str, batch_size: int, rng: random.Random) -> list[list[tuple[str, str]]]:
    spec = PACKS[pack]
    items: list[list[tuple[str, str]]] = []
    for _ in range(batch_size):
        pairs = [(label, generator(rng)) for label, generator in spec["slots"]]
        items.append(pairs)
    return items


def build_prompt(pack: str, items: list[list[tuple[str, str]]]) -> str:
    spec = PACKS[pack]
    lines = []
    for index, pairs in enumerate(items, start=1):
        values = " | ".join(
            f"{LABEL_DISPLAY.get(label, label)}: {value}"
            for label, value in pairs
        )
        lines.append(f"{index}. {values}")
    return (
        f"Πακέτο: {pack}\n"
        f"Ύφος/στόχος: {spec['description']}\n\n"
        f"Γράψε ΑΚΡΙΒΩΣ {len(items)} αριθμημένα ελληνικά κείμενα, ένα ανά γραμμή.\n"
        "Κάθε κείμενο πρέπει να περιέχει όλες τις τιμές της αντίστοιχης γραμμής "
        "ΑΥΤΟΥΣΙΕΣ, με ίδια σημεία στίξης, κενά, κεφαλαία και πεζά.\n\n"
        "Τιμές:\n"
        + "\n".join(lines)
        + "\n\nΚανόνες:\n"
        "- Μία γραμμή ανά κείμενο, μορφή «1. ...», «2. ...».\n"
        "- 18-55 λέξεις ανά κείμενο.\n"
        "- Όχι markdown, όχι εισαγωγικά, όχι σχόλια.\n"
        "- Αν δύο αριθμητικές τιμές μοιάζουν μεταξύ τους, βάλε καθαρό τοπικό δείκτη."
    )


def parse_records(content: str, items: list[list[tuple[str, str]]], pack: str) -> list[dict]:
    lines: dict[int, str] = {}
    for line in content.splitlines():
        match = NUM_LINE_RE.match(line)
        if not match:
            continue
        index = int(match.group(1)) - 1
        text = match.group(2).strip()
        if 0 <= index < len(items) and text and index not in lines:
            lines[index] = text

    records: list[dict] = []
    for index, pairs in enumerate(items):
        text = lines.get(index)
        if not text:
            continue
        labels = []
        ok = True
        for category, value in pairs:
            start = text.find(value)
            if start < 0:
                ok = False
                break
            labels.append({"category": category, "start": start, "end": start + len(value)})
        if not ok:
            continue
        labels.sort(key=lambda item: item["start"])
        records.append(
            {
                "text": text,
                "label": labels,
                "info": {
                    "source": "local_qwen_contrastive_v2_13",
                    "difficulty": "hard",
                    "domain": f"contrastive:{pack}",
                    "strategy": "llm-server/qwen/local",
                    "license_basis": "local Apache-compatible generator; deterministic fictional PII slots",
                },
            }
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pack", choices=sorted(PACKS), required=True)
    parser.add_argument("--target-count", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=2033)
    parser.add_argument("--engine", choices=("ollama", "openai"), default="openai")
    parser.add_argument("--host", default=None)
    parser.add_argument("--model", default="qwen")
    parser.add_argument("--max-batches", type=int, default=200)
    parser.add_argument("--max-tokens", type=int, default=2200)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append to an existing output file until target-count total rows exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host is None:
        args.host = "http://localhost:11434" if args.engine == "ollama" else "http://localhost:8080"
    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    mode = "w"
    if args.resume and args.output.exists():
        with args.output.open("r", encoding="utf-8") as handle:
            written = sum(1 for _ in handle)
        mode = "a"
        print(
            f"[resume] {args.output} already has {written} rows; "
            f"target={args.target_count}",
            flush=True,
        )
    skipped = 0
    batches = 0
    started = time.time()
    with args.output.open(mode, encoding="utf-8") as handle:
        while written < args.target_count and batches < args.max_batches:
            batches += 1
            items = make_items(args.pack, args.batch_size, rng)
            prompt = build_prompt(args.pack, items)
            try:
                before = time.time()
                content = call_local_model(
                    args.engine,
                    args.host,
                    args.model,
                    prompt,
                    max_tokens=args.max_tokens,
                )
                elapsed = time.time() - before
            except Exception as exc:
                print(f"[batch {batches}] local model call failed: {exc}", flush=True)
                continue
            records = parse_records(content, items, args.pack)
            for record in records:
                if written >= args.target_count:
                    break
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
            handle.flush()
            skipped += args.batch_size - len(records)
            print(
                f"[batch {batches:03d}] +{len(records)}/{args.batch_size} "
                f"written={written}/{args.target_count} call={elapsed:.1f}s",
                flush=True,
            )

    print(
        f"DONE pack={args.pack} written={written} skipped={skipped} "
        f"batches={batches} minutes={(time.time() - started) / 60:.1f}"
    )


if __name__ == "__main__":
    main()
