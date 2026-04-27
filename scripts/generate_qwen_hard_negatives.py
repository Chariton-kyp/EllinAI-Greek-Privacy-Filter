"""Generate diverse hard-negative Greek sentences via a local llama-server.

Hard negatives are PII-FREE sentences whose surface form may confuse a
PII detector (contain numbers, capitalized tokens, dates, acronyms,
public-sector identifiers, etc.). They are critical for precision.

The generator calls a local Qwen-style `/v1/chat/completions` endpoint,
asks for batches of N numbered sentences that each look PII-adjacent,
and emits them with empty `label` lists.

Usage:

    python scripts/generate_qwen_hard_negatives.py \
        --output data/processed/hard_neg_qwen.jsonl \
        --count 1500 --batch-size 10 \
        --host http://127.0.0.1:8080 --seed 2024
"""
from __future__ import annotations

import argparse
import json
import random
import re
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


_SYSTEM = (
    "Είσαι βοηθός που γράφει σύντομες ελληνικές προτάσεις-πρότυπα για "
    "ανάπτυξη ανιχνευτή προσωπικών δεδομένων (PII). Σου ζητούν "
    "προτάσεις ΧΩΡΙΣ κανένα προσωπικό δεδομένο (χωρίς ονόματα φυσικών "
    "προσώπων, τηλέφωνα, email, διευθύνσεις, ΑΦΜ, ΑΜΚΑ, ΑΔΤ, IBAN, "
    "αριθμούς λογαριασμών, API keys). Επιστρέφεις ΜΟΝΟ τις προτάσεις, "
    "αριθμημένες 1., 2., ..., χωρίς εισαγωγή, χωρίς εξήγηση."
)


_HARD_NEG_TOPICS = [
    (
        "ορισμοί από νομικά κείμενα",
        "Γράψε προτάσεις-ορισμούς (όπως σε νόμο ή λεξικό) για όρους "
        "δημόσιου ενδιαφέροντος (π.χ. τι είναι ο ΑΦΜ, τι είναι η ΑΜΚΑ, "
        "τι είναι ο IBAN, τι είναι το ΦΠΑ). Χωρίς συγκεκριμένους αριθμούς.",
    ),
    (
        "στατιστικά ΕΛΣΤΑΤ / ΑΑΔΕ",
        "Γράψε προτάσεις που αναφέρουν δημοσιευμένα στατιστικά στοιχεία "
        "της Ελληνικής Στατιστικής Αρχής ή άλλων δημοσίων φορέων. "
        "Ποσοστά, σύνολα, χρονιές είναι ΟΚ, όχι όμως πραγματικοί αριθμοί "
        "ταυτότητας / τηλεφώνου / ΑΦΜ.",
    ),
    (
        "πρόσωπα ιστορικών γεγονότων",
        "Γράψε προτάσεις για ιστορικά πρόσωπα ή δημόσια πρόσωπα "
        "(πολιτικοί, καλλιτέχνες, επιστήμονες) ως μέρος ιστορικής ή "
        "ειδησεογραφικής αναφοράς. Τα ονόματα ΔΕΝ θεωρούνται PII σε αυτό "
        "το πλαίσιο.",
    ),
    (
        "τεχνικός λόγος / κώδικας",
        "Γράψε προτάσεις τεχνικού περιεχομένου για προγραμματισμό, APIs, "
        "εργαλεία, κωδικούς σφάλματος. Χωρίς πραγματικά secrets / tokens.",
    ),
    (
        "επιστημονικά / γεωγραφικά γεγονότα",
        "Γράψε προτάσεις που αναφέρουν επιστημονικά ή γεωγραφικά γεγονότα "
        "(π.χ. απόσταση πλανητών, πληθυσμός χωρών, ύψος βουνών). "
        "Αριθμοί ΟΚ αλλά όχι PII.",
    ),
    (
        "διαχειριστικά συστήματα",
        "Γράψε προτάσεις για κανόνες διαχείρισης λογαριασμών, συστημάτων, "
        "διαδικασιών (π.χ. «ο αριθμός αίτησης παράγεται αυτόματα από το "
        "σύστημα»). Χωρίς συγκεκριμένα στοιχεία.",
    ),
    (
        "εταιρείες και εμπορικά σήματα",
        "Γράψε προτάσεις που αναφέρουν εταιρείες, εμπορικά σήματα ή "
        "οργανισμούς ως δημόσιες οντότητες (OpenAI, Microsoft, ΔΕΗ, ΟΤΕ). "
        "Τα ονόματα εταιρειών δεν είναι PII.",
    ),
    (
        "κοινές φράσεις με αριθμούς",
        "Γράψε προτάσεις που περιέχουν γενικούς αριθμούς (ποσοστά, "
        "ποσότητες, ταχύτητα, ώρες, χρόνο), όπου ο αριθμός ΔΕΝ είναι ΑΦΜ / "
        "ΑΜΚΑ / ΑΔΤ / IBAN / τηλέφωνο. Π.χ. «Το τμήμα λειτουργεί 8 ώρες "
        "την ημέρα».",
    ),
    (
        "αθλητικά αποτελέσματα",
        "Γράψε προτάσεις από αθλητικά δελτία ειδήσεων (σκορ, βαθμολογίες, "
        "διοργανώσεις, χρόνοι). Οι αριθμοί αφορούν αθλητικά δεδομένα, όχι "
        "προσωπικά.",
    ),
    (
        "συνταγές μαγειρικής",
        "Γράψε προτάσεις από συνταγές (ποσότητες, θερμοκρασία φούρνου, "
        "χρόνος ψησίματος). Καμία αναφορά σε πραγματικό πρόσωπο.",
    ),
    (
        "οικονομικές ειδήσεις / χρηματιστήριο",
        "Γράψε προτάσεις από οικονομικά ρεπορτάζ: αποτιμήσεις, μέση "
        "απόδοση μετοχών, ποσοστά πληθωρισμού. Όχι ιδιωτικοί τραπεζικοί "
        "λογαριασμοί.",
    ),
    (
        "εκπαιδευτικό περιεχόμενο",
        "Γράψε προτάσεις από διδακτικό υλικό ή εκπαιδευτικές ανακοινώσεις "
        "(κλίμακες βαθμολογίας, ώρες μαθημάτων, θεωρητικοί τύποι). Όχι "
        "προσωπικά στοιχεία μαθητή.",
    ),
    (
        "σφάλματα συστήματος / logging",
        "Γράψε προτάσεις-μηνύματα σφαλμάτων ή log entries (timestamp-"
        "like, κωδικοί HTTP, process IDs). Χωρίς πραγματικά credentials.",
    ),
    (
        "γεωγραφικές διευθύνσεις μνημείων",
        "Γράψε προτάσεις που αναφέρουν διευθύνσεις δημόσιων μνημείων, "
        "μουσείων ή αξιοθέατων. Αυτές είναι δημόσιες πληροφορίες, όχι "
        "προσωπικές διευθύνσεις.",
    ),
]


_NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)[.\)]\s*(.+?)\s*$")
_WRAPPER_LEADERS = (
    "Παράδειγμα:", "Σίγουρα!", "Φυσικά!", "Βεβαίως!",
    "Ορίστε:", "Ιδού:", "Ένα παράδειγμα",
)


def _strip_wrappers(s: str) -> str:
    s = s.strip()
    for prefix in ("- ", "• ", "— ", "* ", "\"", "«", "'", "`"):
        if s.startswith(prefix):
            s = s[len(prefix):].lstrip()
    for suffix in ("\"", "»", "'", "`"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    return s.strip()


def call_server(host: str, system: str, user: str, seed: int,
                max_tokens: int = 1024, timeout: float = 180.0) -> str:
    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "temperature": 0.8,
        "seed": seed,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        f"{host.rstrip('/')}/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8"))
    choices = payload.get("choices") or []
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "")


def generate_batch(rng: random.Random, host: str, batch_size: int) -> list[str]:
    topic_name, topic_instruction = rng.choice(_HARD_NEG_TOPICS)
    user = (
        f"Θέμα: {topic_name}\n{topic_instruction}\n\n"
        f"Γράψε ΑΚΡΙΒΩΣ {batch_size} σύντομες, φυσικές ελληνικές προτάσεις "
        "που εμπίπτουν στο θέμα. Κάθε πρόταση 8-20 λέξεις, αριθμημένη "
        "«1.», «2.», ..., χωρίς προσωπικά δεδομένα, χωρίς εισαγωγή."
    )
    try:
        content = call_server(host, _SYSTEM, user, rng.randint(0, 2**31 - 1))
    except Exception as exc:  # noqa: BLE001
        print(f"[hard-neg gen] server error: {exc}")
        return []
    out: list[str] = []
    for line in content.splitlines():
        m = _NUMBERED_LINE_RE.match(line)
        if not m:
            continue
        sentence = _strip_wrappers(m.group(2))
        if 30 <= len(sentence) <= 260 and len(sentence.split()) >= 5:
            out.append(sentence)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    p.add_argument("--count", type=int, default=1500)
    p.add_argument("--batch-size", type=int, default=10)
    p.add_argument("--host", default="http://127.0.0.1:8080")
    p.add_argument("--seed", type=int, default=2024)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    seen_texts: set[str] = set()
    with out.open("w", encoding="utf-8") as fp:
        while written < args.count:
            batch = generate_batch(rng, args.host, args.batch_size)
            for sentence in batch:
                if sentence in seen_texts:
                    continue
                seen_texts.add(sentence)
                record = {
                    "text": sentence,
                    "label": [],
                    "info": {
                        "difficulty": "hard_negative",
                        "domain": "qwen_hard_neg",
                        "source": "commercial_safe_generator",
                        "strategy": "qwen_hard_negative",
                    },
                }
                fp.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
                if written >= args.count:
                    break
    print(f"Wrote {written} hard-negative records to {out}")


if __name__ == "__main__":
    main()
