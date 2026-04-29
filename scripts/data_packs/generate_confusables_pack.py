"""Generate v2.5 confusable hard-negatives pack.

Targets the v2 model's class-confusion errors from triage:
  - gemi (12) confused with account_number (12-digit overlap)
  - driver_license (11) confused with adt (Greek-letter + digits)
  - pcn (11) confused with account_number/afm
  - imei (7) confused with account_number (long digit string)
  - passport (4) confused with adt

Each record places a confusable VALUE adjacent to its DISTINGUISHING
PREFIX in a carrier sentence. Goal: force the model to learn the prefix
token as a strong signal for the class.

Usage:
    python scripts/data_packs/generate_confusables_pack.py \\
        --output data/processed/confusables_pack.jsonl --count 10000
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

# Reuse Tier-1 generators for shape-correct values
from generate_tier1_records import (
    GREEK_PLATE_LETTERS,
    gen_pcn,
)


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choices(string.digits, k=n))


def gen_account_number(rng: random.Random) -> str:
    """Generate a Greek-style 12-digit account number with separators."""
    a = _digits(rng, 4)
    b = _digits(rng, 5)
    c = _digits(rng, 3)
    return f"{a}-{b}-{c}"


def gen_account_number_compact(rng: random.Random) -> str:
    return _digits(rng, 12)


def gen_afm(rng: random.Random) -> str:
    return _digits(rng, 9)


def gen_imei(rng: random.Random) -> str:
    return _digits(rng, 15)


def gen_gemi(rng: random.Random) -> str:
    """ΓΕΜΗ format: 12 digits."""
    return _digits(rng, 12)


def gen_dl(rng: random.Random) -> str:
    """Driver license: 9 digits OR Greek letters + digits."""
    if rng.random() < 0.5:
        return _digits(rng, 9)
    letters = "".join(rng.choices(GREEK_PLATE_LETTERS, k=2))
    digits = _digits(rng, 6)
    return f"{letters}-{digits}"


def gen_adt(rng: random.Random) -> str:
    """ADT: 1-2 Greek letters + 6 digits, optional dash."""
    n = rng.choice([1, 2])
    letters = "".join(rng.choices(GREEK_PLATE_LETTERS, k=n))
    sep = rng.choice(["-", ""])
    digits = _digits(rng, 6)
    return f"{letters}{sep}{digits}"


def gen_passport(rng: random.Random) -> str:
    """Greek passport: 1-2 Greek letters + 7 digits."""
    letters = "".join(rng.choices(GREEK_PLATE_LETTERS + "ABCDEFG", k=rng.choice([1, 2])))
    digits = _digits(rng, 7)
    return f"{letters}{digits}"


def gen_phone(rng: random.Random) -> str:
    """Greek phone: mobile (69x...) or landline (21x..., 23x..., etc.)."""
    style = rng.random()
    if style < 0.55:
        # Mobile
        return "69" + _digits(rng, 8)
    elif style < 0.85:
        # Landline 10-digit (210, 211, 22x...)
        prefix = rng.choice(["210", "211", "213", "23", "24", "25", "26", "27", "28"])
        suffix = _digits(rng, 10 - len(prefix))
        return prefix + suffix
    else:
        # International prefix
        return "+30 " + ("69" + _digits(rng, 8)
                          if rng.random() < 0.5
                          else "210 " + _digits(rng, 7))


def gen_amka(rng: random.Random) -> str:
    """AMKA: 11-digit, first 6 digits = DDMMYY."""
    return _digits(rng, 11)


def gen_ama(rng: random.Random) -> str:
    """AMA IKA: 7-digit."""
    return _digits(rng, 7)


def gen_plate(rng: random.Random) -> str:
    """Greek license plate: 3 Greek letters + 4 digits."""
    letters = "".join(rng.choices(GREEK_PLATE_LETTERS, k=3))
    sep = rng.choice(["-", " ", ""])
    digits = _digits(rng, 4)
    return f"{letters}{sep}{digits}"


def gen_vin(rng: random.Random) -> str:
    """ISO 3779 VIN: 17 chars Latin alphanum (no I/O/Q)."""
    alphabet = "ABCDEFGHJKLMNPRSTUVWXYZ" + string.digits
    return "".join(rng.choices(alphabet, k=17))


# Confusable PAIR templates: each element is a "pair" — one example of
# class A and one of class B in the same text, both with their canonical
# distinguishing prefix. This forces the model to attend to the prefix.

PAIRS = [
    # gemi vs account_number (both 12-digit-ish)
    {
        "template": "Η εταιρεία με ΓΕΜΗ {GEMI} χρησιμοποιεί τον λογαριασμό {ACC}.",
        "spans": [("gemi", "{GEMI}"), ("account_number", "{ACC}")],
        "gen_fns": {"GEMI": gen_gemi, "ACC": gen_account_number},
    },
    {
        "template": "ΓΕΜΗ: {GEMI} | Λογ.: {ACC}",
        "spans": [("gemi", "{GEMI}"), ("account_number", "{ACC}")],
        "gen_fns": {"GEMI": gen_gemi, "ACC": gen_account_number_compact},
    },
    {
        "template": "Σας υπενθυμίζουμε ότι ο ΓΕΜΗ της εταιρείας είναι {GEMI} και ο τραπεζικός λογαριασμός {ACC}.",
        "spans": [("gemi", "{GEMI}"), ("account_number", "{ACC}")],
        "gen_fns": {"GEMI": gen_gemi, "ACC": gen_account_number},
    },
    {
        "template": "Πληρωμή στο ΓΕΜΗ {GEMI}, IBAN συνδεδεμένος με τον αριθμό {ACC}.",
        "spans": [("gemi", "{GEMI}"), ("account_number", "{ACC}")],
        "gen_fns": {"GEMI": gen_gemi, "ACC": gen_account_number},
    },

    # driver_license vs adt (both Greek-letter + digits)
    {
        "template": "Ταυτότητα: ΑΔΤ {ADT}, Δίπλωμα οδήγησης: {DL}.",
        "spans": [("adt", "{ADT}"), ("driver_license", "{DL}")],
        "gen_fns": {"ADT": gen_adt, "DL": gen_dl},
    },
    {
        "template": "Στοιχεία οδηγού: αρ. ταυτότητας ΑΔΤ {ADT}, αρ. διπλώματος {DL}.",
        "spans": [("adt", "{ADT}"), ("driver_license", "{DL}")],
        "gen_fns": {"ADT": gen_adt, "DL": gen_dl},
    },
    {
        "template": "ΑΔΤ {ADT} | Δίπλωμα οδ. {DL}",
        "spans": [("adt", "{ADT}"), ("driver_license", "{DL}")],
        "gen_fns": {"ADT": gen_adt, "DL": gen_dl},
    },
    {
        "template": "Ο/Η κάτοχος προσκόμισε ΑΔΤ ΑΔΤ {ADT} καθώς και δίπλωμα {DL}.",
        "spans": [("adt", "{ADT}"), ("driver_license", "{DL}")],
        "gen_fns": {"ADT": gen_adt, "DL": gen_dl},
    },

    # pcn vs afm (similar 9-digit core)
    {
        "template": "Στοιχεία πολίτη: ΑΦΜ {AFM}, ΠΑΠ {PCN}.",
        "spans": [("afm", "{AFM}"), ("pcn", "{PCN}")],
        "gen_fns": {"AFM": gen_afm, "PCN": gen_pcn},
    },
    {
        "template": "Πιστοποίηση: PCN {PCN} και ΑΦΜ {AFM}.",
        "spans": [("pcn", "{PCN}"), ("afm", "{AFM}")],
        "gen_fns": {"PCN": gen_pcn, "AFM": gen_afm},
    },
    {
        "template": "ΑΦΜ: {AFM} | Προσωπικός Αριθμός Πολίτη: {PCN}",
        "spans": [("afm", "{AFM}"), ("pcn", "{PCN}")],
        "gen_fns": {"AFM": gen_afm, "PCN": gen_pcn},
    },
    {
        "template": "Επικυρωμένη ΠΑΠ {PCN}, αντίστοιχη ΑΦΜ {AFM}.",
        "spans": [("pcn", "{PCN}"), ("afm", "{AFM}")],
        "gen_fns": {"PCN": gen_pcn, "AFM": gen_afm},
    },

    # imei vs account_number (both 12-15 digit strings)
    {
        "template": "Συσκευή με IMEI {IMEI}, λογαριασμός χρέωσης {ACC}.",
        "spans": [("imei", "{IMEI}"), ("account_number", "{ACC}")],
        "gen_fns": {"IMEI": gen_imei, "ACC": gen_account_number},
    },
    {
        "template": "IMEI: {IMEI} / λογ.: {ACC}",
        "spans": [("imei", "{IMEI}"), ("account_number", "{ACC}")],
        "gen_fns": {"IMEI": gen_imei, "ACC": gen_account_number_compact},
    },
    {
        "template": "Καταγραφή συσκευής: IMEI {IMEI}, χρεωμένος λογαριασμός {ACC}.",
        "spans": [("imei", "{IMEI}"), ("account_number", "{ACC}")],
        "gen_fns": {"IMEI": gen_imei, "ACC": gen_account_number},
    },

    # passport vs adt (both letter+digit shape)
    {
        "template": "Διαβατήριο {PASS}, ΑΔΤ {ADT}.",
        "spans": [("passport", "{PASS}"), ("adt", "{ADT}")],
        "gen_fns": {"PASS": gen_passport, "ADT": gen_adt},
    },
    {
        "template": "Έγγραφα ταυτοποίησης: ΑΔΤ {ADT}, διαβατήριο {PASS}.",
        "spans": [("adt", "{ADT}"), ("passport", "{PASS}")],
        "gen_fns": {"ADT": gen_adt, "PASS": gen_passport},
    },
    {
        "template": "Αρ. Διαβ. {PASS} | Αρ. Ταυτ. {ADT}",
        "spans": [("passport", "{PASS}"), ("adt", "{ADT}")],
        "gen_fns": {"PASS": gen_passport, "ADT": gen_adt},
    },

    # afm vs account (both numeric, different prefix)
    {
        "template": "ΑΦΜ {AFM}, λογαριασμός μισθοδοσίας {ACC}.",
        "spans": [("afm", "{AFM}"), ("account_number", "{ACC}")],
        "gen_fns": {"AFM": gen_afm, "ACC": gen_account_number},
    },
    {
        "template": "Φορολογ. στοιχεία ΑΦΜ {AFM} συνδ. με λογ. {ACC}.",
        "spans": [("afm", "{AFM}"), ("account_number", "{ACC}")],
        "gen_fns": {"AFM": gen_afm, "ACC": gen_account_number},
    },

    # Triple confusables — gemi + afm + account
    {
        "template": "Στοιχεία: ΓΕΜΗ {GEMI}, ΑΦΜ {AFM}, λογ. {ACC}.",
        "spans": [("gemi", "{GEMI}"), ("afm", "{AFM}"), ("account_number", "{ACC}")],
        "gen_fns": {"GEMI": gen_gemi, "AFM": gen_afm, "ACC": gen_account_number},
    },
    {
        "template": "ΓΕΜΗ {GEMI} | ΑΦΜ {AFM} | Λογ. {ACC}",
        "spans": [("gemi", "{GEMI}"), ("afm", "{AFM}"), ("account_number", "{ACC}")],
        "gen_fns": {"GEMI": gen_gemi, "AFM": gen_afm, "ACC": gen_account_number_compact},
    },

    # ─── v2.6 negative-pair additions to fix v2.5 regressions ───────

    # phone vs account_number (key regression: phone → account_number 12/15)
    {
        "template": "Τηλ.: {PHONE}, Λογ. {ACC}",
        "spans": [("private_phone", "{PHONE}"), ("account_number", "{ACC}")],
        "gen_fns": {"PHONE": gen_phone, "ACC": gen_account_number_compact},
    },
    {
        "template": "Επικοινωνία: {PHONE} | Αρ. λογαριασμού: {ACC}",
        "spans": [("private_phone", "{PHONE}"), ("account_number", "{ACC}")],
        "gen_fns": {"PHONE": gen_phone, "ACC": gen_account_number},
    },
    {
        "template": "Καλέστε στο {PHONE}. Λογαριασμός χρέωσης: {ACC}.",
        "spans": [("private_phone", "{PHONE}"), ("account_number", "{ACC}")],
        "gen_fns": {"PHONE": gen_phone, "ACC": gen_account_number},
    },
    {
        "template": "Τηλέφωνο επικοινωνίας {PHONE}, λογαριασμός {ACC}.",
        "spans": [("private_phone", "{PHONE}"), ("account_number", "{ACC}")],
        "gen_fns": {"PHONE": gen_phone, "ACC": gen_account_number_compact},
    },

    # phone vs imei (mobile 69x vs 15-digit IMEI)
    {
        "template": "Συσκευή IMEI {IMEI}, αρ. SIM {PHONE}.",
        "spans": [("imei", "{IMEI}"), ("private_phone", "{PHONE}")],
        "gen_fns": {"IMEI": gen_imei, "PHONE": gen_phone},
    },
    {
        "template": "IMEI {IMEI} / Τηλ. {PHONE}",
        "spans": [("imei", "{IMEI}"), ("private_phone", "{PHONE}")],
        "gen_fns": {"IMEI": gen_imei, "PHONE": gen_phone},
    },

    # phone vs amka (mobile 10-digit vs 11-digit AMKA)
    {
        "template": "ΑΜΚΑ {AMKA}, τηλ. επικοινωνίας {PHONE}.",
        "spans": [("amka", "{AMKA}"), ("private_phone", "{PHONE}")],
        "gen_fns": {"AMKA": gen_amka, "PHONE": gen_phone},
    },
    {
        "template": "Επικοινωνία στο τηλ. {PHONE} ή με ΑΜΚΑ {AMKA}.",
        "spans": [("private_phone", "{PHONE}"), ("amka", "{AMKA}")],
        "gen_fns": {"PHONE": gen_phone, "AMKA": gen_amka},
    },

    # ama vs afm (7-digit AMA IKA vs 9-digit AFM)
    {
        "template": "ΑΜΑ ΙΚΑ: {AMA}, ΑΦΜ: {AFM}",
        "spans": [("ama", "{AMA}"), ("afm", "{AFM}")],
        "gen_fns": {"AMA": gen_ama, "AFM": gen_afm},
    },
    {
        "template": "Στοιχεία ασφαλισμένου: ΑΜΑ {AMA}, ΑΦΜ {AFM}.",
        "spans": [("ama", "{AMA}"), ("afm", "{AFM}")],
        "gen_fns": {"AMA": gen_ama, "AFM": gen_afm},
    },
    {
        "template": "ΑΜΑ {AMA} | ΑΦΜ {AFM}",
        "spans": [("ama", "{AMA}"), ("afm", "{AFM}")],
        "gen_fns": {"AMA": gen_ama, "AFM": gen_afm},
    },
    {
        "template": "Νέος ΑΜΑ ασφαλισμένου είναι {AMA} (ΑΦΜ {AFM}).",
        "spans": [("ama", "{AMA}"), ("afm", "{AFM}")],
        "gen_fns": {"AMA": gen_ama, "AFM": gen_afm},
    },

    # license_plate vs adt (Greek letters + digits)
    {
        "template": "Πινακίδα {PLATE}, ΑΔΤ οδηγού {ADT}.",
        "spans": [("license_plate", "{PLATE}"), ("adt", "{ADT}")],
        "gen_fns": {"PLATE": gen_plate, "ADT": gen_adt},
    },
    {
        "template": "Όχημα με πινακίδα {PLATE}, οδηγός με ΑΔΤ {ADT}.",
        "spans": [("license_plate", "{PLATE}"), ("adt", "{ADT}")],
        "gen_fns": {"PLATE": gen_plate, "ADT": gen_adt},
    },
    {
        "template": "Πιν. {PLATE} | ΑΔΤ {ADT}",
        "spans": [("license_plate", "{PLATE}"), ("adt", "{ADT}")],
        "gen_fns": {"PLATE": gen_plate, "ADT": gen_adt},
    },

    # license_plate vs vehicle_vin (plate 7-char vs 17-char VIN)
    {
        "template": "Πινακίδα {PLATE}, αρ. πλαισίου {VIN}.",
        "spans": [("license_plate", "{PLATE}"), ("vehicle_vin", "{VIN}")],
        "gen_fns": {"PLATE": gen_plate, "VIN": gen_vin},
    },
    {
        "template": "Όχημα {PLATE} VIN {VIN}",
        "spans": [("license_plate", "{PLATE}"), ("vehicle_vin", "{VIN}")],
        "gen_fns": {"PLATE": gen_plate, "VIN": gen_vin},
    },
    {
        "template": "Πινακίδα κυκλοφορίας {PLATE} | πλαίσιο {VIN}",
        "spans": [("license_plate", "{PLATE}"), ("vehicle_vin", "{VIN}")],
        "gen_fns": {"PLATE": gen_plate, "VIN": gen_vin},
    },

    # phone-only frames (no confusable, just reinforcement)
    {
        "template": "Επικοινωνία: {PHONE}",
        "spans": [("private_phone", "{PHONE}")],
        "gen_fns": {"PHONE": gen_phone},
    },
    {
        "template": "Τηλέφωνο: {PHONE}",
        "spans": [("private_phone", "{PHONE}")],
        "gen_fns": {"PHONE": gen_phone},
    },
    {
        "template": "Καλέστε {PHONE}",
        "spans": [("private_phone", "{PHONE}")],
        "gen_fns": {"PHONE": gen_phone},
    },

    # plate-only reinforcement frames
    {
        "template": "Πινακίδα: {PLATE}",
        "spans": [("license_plate", "{PLATE}")],
        "gen_fns": {"PLATE": gen_plate},
    },
    {
        "template": "Όχημα {PLATE} σταθμευμένο.",
        "spans": [("license_plate", "{PLATE}")],
        "gen_fns": {"PLATE": gen_plate},
    },

    # ama-only reinforcement
    {
        "template": "ΑΜΑ ΙΚΑ: {AMA}",
        "spans": [("ama", "{AMA}")],
        "gen_fns": {"AMA": gen_ama},
    },
    {
        "template": "Αρ. Μητρώου Ασφάλισης: {AMA}",
        "spans": [("ama", "{AMA}")],
        "gen_fns": {"AMA": gen_ama},
    },
]


def generate_record(rng: random.Random) -> dict:
    pair = rng.choice(PAIRS)
    template = pair["template"]
    placeholders: dict[str, str] = {}
    for key, gen in pair["gen_fns"].items():
        placeholders[key] = gen(rng)
    text = template
    for key, val in placeholders.items():
        text = text.replace("{" + key + "}", val)
    labels = []
    cursor = 0
    for label, placeholder in pair["spans"]:
        key = placeholder.strip("{}")
        val = placeholders[key]
        idx = text.find(val, cursor)
        if idx == -1:
            idx = text.find(val)
        labels.append({"category": label, "start": idx, "end": idx + len(val)})
        cursor = idx + len(val)
    return {"text": text, "label": labels,
            "info": {"source": "v2_5_confusables_pack", "domain": "hard_negative"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1338)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(args.output, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            rec = generate_record(rng)
            ok = all(
                rec["text"][lab["start"]:lab["end"]]
                for lab in rec["label"]
            )
            if not ok:
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written} confusables-pack records to {args.output}")


if __name__ == "__main__":
    main()
