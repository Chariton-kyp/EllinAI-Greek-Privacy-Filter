"""Generate v2.5 CVV + URL recall pack.

Targets v2 model's miss rate:
  - cvv: 8/10 missed (3-digit too generic)
  - private_url: 11 missed + 3 boundary (prefix retention)
  - secret: 4 confusion + 2 boundary

Strategy:
  - card_pan + cvv adjacency: every record contains a card_pan + cvv
    pair with explicit CVV/CVC2/CVV2 marker so the model learns the
    marker token strongly anchors the 3-digit class.
  - URL pack: full https://... in dense punctuation contexts to teach
    the model to extend boundaries from prefix to query string.
  - Secret pack: alphanumeric tokens 20-50 chars after API_KEY=,
    SECRET=, token=, etc.

Usage:
    python scripts/data_packs/generate_cvv_url_pack.py \\
        --output data/processed/cvv_url_pack.jsonl --count 5000
"""
from __future__ import annotations

import argparse
import json
import random
import string
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def luhn_check_digit(digits: str) -> str:
    s = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return str((10 - s % 10) % 10)


def gen_card_pan(rng: random.Random) -> str:
    """Luhn-valid 16-digit PAN with random brand prefix."""
    brand = rng.choice(["4", "5", "37"])
    body_len = 15 - len(brand)
    body = "".join(rng.choices(string.digits, k=body_len))
    base = brand + body
    full = base + luhn_check_digit(base)
    sep = rng.choice([" ", "", "-"])
    if sep == "":
        return full
    return f"{full[0:4]}{sep}{full[4:8]}{sep}{full[8:12]}{sep}{full[12:16]}"


def gen_cvv(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=3))


def _random_path_segment(rng: random.Random, n: int = 8) -> str:
    return "".join(rng.choices(string.ascii_lowercase + string.digits, k=n))


def gen_url(rng: random.Random) -> str:
    """Generate URL with various complexity levels."""
    scheme = rng.choice(["https", "http"])
    domain_root = rng.choice([
        "example.gr", "company-hellas.gr", "shop.gr", "bank-online.gr",
        "intranet.firm.gr", "portal.greek-co.gr", "app.tax.gov.gr",
        "auth.platform.gr", "github.com", "linkedin.com",
        "secure.payments-gr.com", "docs.api-platform.gr",
    ])
    path_parts = []
    n_parts = rng.choice([1, 2, 3])
    for _ in range(n_parts):
        path_parts.append(_random_path_segment(rng, rng.choice([4, 6, 8, 12])))
    path = "/" + "/".join(path_parts) if path_parts else ""
    if rng.random() < 0.3:
        # add query string
        n_qs = rng.choice([1, 2])
        qs_parts = []
        for _ in range(n_qs):
            key = rng.choice(["id", "token", "ref", "session", "user", "q"])
            val = _random_path_segment(rng, 8)
            qs_parts.append(f"{key}={val}")
        path += "?" + "&".join(qs_parts)
    return f"{scheme}://{domain_root}{path}"


def gen_secret(rng: random.Random) -> str:
    """Generate alphanum secret 20-48 chars."""
    n = rng.choice([20, 24, 28, 32, 40, 48])
    alphabet = string.ascii_letters + string.digits + "_"
    prefix = rng.choice(["tk_live_", "tk_test_", "gpat_", "AKIA", "Bearer ",
                          "tok_", "key_", "whsec_", ""])
    body = "".join(rng.choices(alphabet, k=n))
    return prefix + body


# ─── Templates ────────────────────────────────────────────────────────

CVV_TEMPLATES = [
    "Πληρωμή με κάρτα {PAN} και CVV {CVV} επιτυχής.",
    "Στοιχεία κάρτας: {PAN}, CVV2: {CVV}, λήξη 12/29.",
    "Αρ. κάρτας {PAN} (CVV {CVV}). Παρακαλώ μην το κοινοποιήσετε.",
    "Visa: {PAN} | CVC: {CVV}",
    "Επιβεβαίωση πληρωμής. Κάρτα ****{PAN_LAST4} (πλήρης {PAN}, CVV {CVV}).",
    "Καταχώρηση: {PAN} CVV {CVV} (3-ψήφιος κωδ. ασφαλείας).",
    "Πληροφορίες κάρτας: number={PAN}, cvv={CVV}, expiry=11/27.",
    "MasterCard {PAN} cvc {CVV}.",
    "Αρ. πληρωμής: {PAN}, ασφαλείας 3 ψηφίων: {CVV}.",
    "Card-pan: {PAN}\nCVV: {CVV}",
]

URL_TEMPLATES = [
    "Επισκεφθείτε τον σύνδεσμο {URL} για περισσότερα.",
    "Δείτε λεπτομέρειες στο {URL}.",
    "Πατήστε εδώ: {URL}",
    "Πηγή: {URL}",
    "Ο σύνδεσμος {URL} είναι ενεργός.",
    "({URL}) — δοκιμάστε το!",
    "URL: {URL}\n",
    "Στείλτε αναφορά μέσω {URL}.",
    "Σύνδεσμος ανάκτησης: {URL}.",
    "Πληροφορίες: <{URL}>",
    "Δες αυτό!! {URL} :)",
    "Επιβεβαίωση: {URL}.",
    "Αναφορά #4567 στο {URL}",
]

SECRET_TEMPLATES = [
    "Κωδικός API: {SECRET}",
    "API_KEY={SECRET}",
    "SECRET={SECRET}",
    "TOKEN: {SECRET}",
    "Παρακαλώ μην κοινοποιείτε τον κωδικό {SECRET}.",
    "Authorization: Bearer {SECRET}",
    "ΣΥΝΘΗΜΑΤΙΚΟ: {SECRET}",
    "X-Auth-Token: {SECRET}",
    "credentials.token = '{SECRET}';",
    "Έλεγχος: token=\"{SECRET}\".",
    "ENV: SESSION_SECRET={SECRET}",
    "Παράδοση κωδικού πρόσβασης: {SECRET}",
    "Νέος προσωπικός κωδικός {SECRET} — σημείωσέ τον.",
]


def generate_cvv_record(rng: random.Random) -> dict:
    template = rng.choice(CVV_TEMPLATES)
    pan = gen_card_pan(rng)
    cvv = gen_cvv(rng)
    text = template.replace("{PAN}", pan).replace("{CVV}", cvv)
    text = text.replace("{PAN_LAST4}", pan[-4:])
    labels = []
    pi = text.find(pan)
    if pi != -1:
        labels.append({"category": "card_pan", "start": pi, "end": pi + len(pan)})
    ci = text.find(cvv, pi + len(pan) if pi != -1 else 0)
    if ci != -1:
        labels.append({"category": "cvv", "start": ci, "end": ci + len(cvv)})
    return {"text": text, "label": labels,
            "info": {"source": "v2_5_cvv_url_pack", "domain": "card_payment"}}


def generate_url_record(rng: random.Random) -> dict:
    template = rng.choice(URL_TEMPLATES)
    url = gen_url(rng)
    text = template.replace("{URL}", url)
    idx = text.find(url)
    labels = [{"category": "private_url", "start": idx, "end": idx + len(url)}]
    return {"text": text, "label": labels,
            "info": {"source": "v2_5_cvv_url_pack", "domain": "url_carrier"}}


def generate_secret_record(rng: random.Random) -> dict:
    template = rng.choice(SECRET_TEMPLATES)
    secret = gen_secret(rng)
    text = template.replace("{SECRET}", secret)
    idx = text.find(secret)
    labels = [{"category": "secret", "start": idx, "end": idx + len(secret)}]
    return {"text": text, "label": labels,
            "info": {"source": "v2_5_cvv_url_pack", "domain": "secret_carrier"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1339)
    parser.add_argument("--cvv-fraction", type=float, default=0.4)
    parser.add_argument("--url-fraction", type=float, default=0.3)
    parser.add_argument("--secret-fraction", type=float, default=0.3)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(args.output, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            roll = rng.random()
            if roll < args.cvv_fraction:
                rec = generate_cvv_record(rng)
            elif roll < args.cvv_fraction + args.url_fraction:
                rec = generate_url_record(rng)
            else:
                rec = generate_secret_record(rng)
            ok = all(
                rec["text"][lab["start"]:lab["end"]]
                for lab in rec["label"]
            )
            if not ok:
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written} cvv_url_pack records to {args.output}")


if __name__ == "__main__":
    main()
