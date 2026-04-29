"""Generate v2.10 recall-boost pack.

v2.9 made the model too conservative on numeric classes:
  - ama            0.133 (1/12 TP)
  - amka           0.632 (12 missed)
  - afm            0.832 (14 missed)
  - gemi           0.593 (3 missed + 4 confusion)
  - driver_license 0.667 (6 missed)
  - ip_address     0.741 (6 missed)

This pack injects PURE POSITIVE EXAMPLES (no negatives, no confusables)
in diverse Greek contexts — narrative, dense-PII, minimal-prefix, emoji
prefix — to recover recall while preserving v2.9 precision gains.

Usage:
    python scripts/data_packs/generate_v2_10_recall_pack.py \\
        --output data/processed/v2_10_recall_pack.jsonl \\
        --count 14000 --seed 2030
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
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "data_packs"))

from greek_names import compose_name


# ─── Value generators ───────────────────────────────────────────────

def gen_afm(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=9))


def gen_ama(rng: random.Random) -> str:
    """AMA ΙΚΑ: 7 digits OR ΕΦΚΑ legacy 9 digits."""
    return "".join(rng.choices(string.digits, k=rng.choice([7, 9])))


def gen_amka(rng: random.Random) -> str:
    """11-digit AMKA, first 6 = DDMMYY-ish."""
    return "".join(rng.choices(string.digits, k=11))


def gen_gemi(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=12))


def gen_dl(rng: random.Random) -> str:
    """Greek DL: 9 digits canonical."""
    return "".join(rng.choices(string.digits, k=9))


def gen_ipv4(rng: random.Random) -> str:
    return ".".join(str(rng.randint(1, 254)) for _ in range(4))


def gen_ipv6(rng: random.Random) -> str:
    return ":".join(f"{rng.randint(0, 0xFFFF):04x}" for _ in range(8))


def gen_ip(rng: random.Random) -> str:
    return gen_ipv4(rng) if rng.random() < 0.85 else gen_ipv6(rng)


# ─── AMA recall (BIGGEST WEAKNESS) ──────────────────────────────────

_AMA_FRAMES = [
    "ΑΜΑ ΙΚΑ: {V}",
    "ΑΜΑ: {V}",
    "Αρ. Μητρώου Ασφάλισης ΙΚΑ {V}.",
    "Αρ. Μητρώου ΙΚΑ-ΕΤΑΜ: {V}",
    "Ασφαλισμένος με ΑΜΑ {V} εργάζεται ως πωλητής.",
    "Ο ΑΜΑ της εταιρείας είναι {V}.",
    "Στο βιβλιάριο εμφανίζεται ΑΜΑ ΙΚΑ {V}.",
    "Ανανέωση ασφάλισης: ΑΜΑ {V}.",
    "Καταχώρηση ΕΦΚΑ — ΑΜΑ {V}.",
    "Ο εργοδότης δήλωσε ΑΜΑ ΙΚΑ {V} για τον εργαζόμενο.",
    "Έλεγχος ΑΜΑ {V} ολοκληρώθηκε.",
    "Νέος ασφαλισμένος ΑΜΑ ΙΚΑ {V}.",
    "Στοιχεία ΕΦΚΑ: ΑΜΑ {V}.",
    "ΑΜΑ ΙΚΑ {V} -- επιτυχής επαλήθευση.",
    "Ο/Η ασφαλισμένος/-η με ΑΜΑ {V} έχει 25 έτη υπηρεσίας.",
    "Πιστοποίηση ΑΜΑ ΙΚΑ {V} έγινε αποδεκτή.",
    "ΑΜΑ ΙΚΑ {V} | καθεστώς: ενεργό",
    "[ΑΜΑ {V}]",
    "Ασφαλιστικός φορέας: ΕΦΚΑ. ΑΜΑ ΙΚΑ {V}.",
    "Καταγραφή χρόνου ασφάλισης για ΑΜΑ {V}: 23 έτη.",
]


def _gen_ama_record(rng: random.Random) -> dict:
    frame = rng.choice(_AMA_FRAMES)
    v = gen_ama(rng)
    text = frame.replace("{V}", v)
    idx = text.find(v)
    return {
        "text": text,
        "label": [{"category": "ama", "start": idx, "end": idx + len(v)}],
        "info": {"source": "v2_10_recall_pack", "domain": "ama_recall"},
    }


# ─── AMKA recall ────────────────────────────────────────────────────

_AMKA_FRAMES = [
    "ΑΜΚΑ: {V}",
    "ΑΜΚΑ {V}",
    "Αρ. Μητρώου Κοινωνικής Ασφάλισης: {V}",
    "Ασθενής με ΑΜΚΑ {V}.",
    "Ο/Η πολίτης με ΑΜΚΑ {V} αιτείται.",
    "Καταχώρηση ΑΜΚΑ {V} στο σύστημα.",
    "ΑΜΚΑ ασφαλισμένου: {V}",
    "Συνταγή για ΑΜΚΑ {V}.",
    "Παραπεμπτικό για ΑΜΚΑ {V}.",
    "Νέος ΑΜΚΑ νεογνού: {V}.",
    "Επιβεβαίωση στοιχείων: ΑΜΚΑ {V}.",
    "Έγκυρος ΑΜΚΑ: {V}.",
    "Δικαιούχος ΑΜΚΑ {V} για το επίδομα.",
    "Καταγραφή ασθενούς. ΑΜΚΑ: {V}.",
    "Στοιχεία ταυτοποίησης ΑΜΚΑ {V}.",
    "ΕΦΚΑ ΑΜΚΑ {V}",
    "[AMKA] {V}",
    "amka: {V}",
    "Ραντεβού στο ΚΕΠ για ΑΜΚΑ {V}.",
    "Πολίτης ΑΜΚΑ {V} -- επιβεβαίωση παραλαβής.",
]


def _gen_amka_record(rng: random.Random) -> dict:
    frame = rng.choice(_AMKA_FRAMES)
    v = gen_amka(rng)
    text = frame.replace("{V}", v)
    idx = text.find(v)
    return {
        "text": text,
        "label": [{"category": "amka", "start": idx, "end": idx + len(v)}],
        "info": {"source": "v2_10_recall_pack", "domain": "amka_recall"},
    }


# ─── AFM recall ─────────────────────────────────────────────────────

_AFM_FRAMES = [
    "ΑΦΜ {V}",
    "ΑΦΜ: {V}",
    "Α.Φ.Μ.: {V}",
    "ΑΦΜ εταιρείας {V}.",
    "Στοιχεία επαγγελματία: ΑΦΜ {V}.",
    "Εκκαθαριστικό για ΑΦΜ {V}.",
    "Φορολογικός κωδικός ΑΦΜ {V}.",
    "Ο φορολογούμενος με ΑΦΜ {V} έχει εκκρεμότητες.",
    "Στη φορολογική δήλωση εμφανίζεται ΑΦΜ {V}.",
    "ΑΦΜ {V} | ΔΟΥ Α' Αθηνών",
    "Ταυτοποίηση ΑΦΜ {V} επιτυχής.",
    "ΑΦΜ φυσικού προσώπου: {V}",
    "ΑΦΜ νομικού προσώπου: {V}",
    "Πληρωτής ΦΠΑ ΑΦΜ {V}.",
    "Καταχώρηση εμπόρου με ΑΦΜ {V}.",
    "[AFM] {V}",
    "afm: {V}",
    "VAT: {V}",
    "Ο/Η αιτών/-ούσα φέρει ΑΦΜ {V}.",
    "Επιστροφή φόρου εγκρίθηκε για ΑΦΜ {V}.",
]


def _gen_afm_record(rng: random.Random) -> dict:
    frame = rng.choice(_AFM_FRAMES)
    v = gen_afm(rng)
    text = frame.replace("{V}", v)
    idx = text.find(v)
    return {
        "text": text,
        "label": [{"category": "afm", "start": idx, "end": idx + len(v)}],
        "info": {"source": "v2_10_recall_pack", "domain": "afm_recall"},
    }


# ─── GEMI recall ────────────────────────────────────────────────────

_GEMI_FRAMES = [
    "ΓΕΜΗ: {V}",
    "ΓΕΜΗ {V}",
    "Αρ. ΓΕΜΗ: {V}.",
    "Γενικό Εμπορικό Μητρώο: {V}",
    "Η εταιρεία με ΓΕΜΗ {V} εδρεύει στην Αθήνα.",
    "Καταχώρηση ΓΕΜΗ {V}.",
    "Ο επιχειρηματίας έλαβε ΓΕΜΗ {V}.",
    "Νέο ΓΕΜΗ: {V}",
    "Στο μητρώο ΓΕΜΗ ο αριθμός {V} αντιστοιχεί.",
    "ΓΕΜΗ {V} | ενεργό",
    "Επιχείρηση με ΓΕΜΗ {V} ολοκλήρωσε αύξηση κεφαλαίου.",
    "Σύσταση ΑΕ. ΓΕΜΗ: {V}.",
    "Στοιχεία επιχείρησης: ΓΕΜΗ {V}.",
    "Πιστοποιητικό ΓΕΜΗ αρ. {V}.",
    "Επιχειρηματικός κωδικός ΓΕΜΗ {V}.",
    "[ΓΕΜΗ] {V}",
    "gemi: {V}",
    "Εγγραφή στο ΓΕΜΗ με αριθμό {V} από την 1/1/2025.",
]


def _gen_gemi_record(rng: random.Random) -> dict:
    frame = rng.choice(_GEMI_FRAMES)
    v = gen_gemi(rng)
    text = frame.replace("{V}", v)
    idx = text.find(v)
    return {
        "text": text,
        "label": [{"category": "gemi", "start": idx, "end": idx + len(v)}],
        "info": {"source": "v2_10_recall_pack", "domain": "gemi_recall"},
    }


# ─── DL recall ──────────────────────────────────────────────────────

_DL_FRAMES = [
    "Δίπλωμα οδήγησης {V}.",
    "Αρ. διπλώματος οδήγησης: {V}",
    "Δίπλωμα: {V}",
    "Δίπλωμα οδήγησης κατηγορίας Β: {V}",
    "Άδεια οδήγησης {V}.",
    "Άδεια οδ. αρ. {V}",
    "Driving licence: {V}",
    "Ο οδηγός με δίπλωμα {V} είχε προηγούμενη κλήση.",
    "Νέο δίπλωμα οδήγησης αρ. {V} εκδόθηκε.",
    "Ανανέωση διπλώματος οδήγησης {V}.",
    "Ικανότητα οδηγού -- δίπλωμα {V}.",
    "Δίπλωμα οδήγησης (Β/Γ): {V}",
    "Έγγραφο: δίπλωμα {V}, ισχύει έως 2030.",
    "Επαγγελματικό δίπλωμα {V} κατηγορίας Δ.",
    "Πιστοποιητικό ικανότητας — δίπλωμα {V}.",
    "DL no. {V}",
    "Δίπλωμα οδ. {V}",
    "Έλεγχος διπλώματος {V} ολοκληρώθηκε.",
]


def _gen_dl_record(rng: random.Random) -> dict:
    frame = rng.choice(_DL_FRAMES)
    v = gen_dl(rng)
    text = frame.replace("{V}", v)
    idx = text.find(v)
    return {
        "text": text,
        "label": [{"category": "driver_license", "start": idx, "end": idx + len(v)}],
        "info": {"source": "v2_10_recall_pack", "domain": "dl_recall"},
    }


# ─── IP recall ──────────────────────────────────────────────────────

_IP_FRAMES = [
    "Σύνδεση από {V}.",
    "IP {V}",
    "Διεύθυνση IP: {V}",
    "Ο διακομιστής {V} αποκρίνεται.",
    "Ζητήσεις από {V}.",
    "Εξωτερική IP {V}.",
    "Εσωτερική IP {V}.",
    "Block IP {V}.",
    "Ping {V}.",
    "Tunnel endpoint {V}.",
    "Στατική IP εργασίας: {V}.",
    "Δυναμική IP {V} αλλάζει κάθε 24 ώρες.",
    "Νέος server IP: {V}",
    "Από: {V}",
    "Source: {V}",
    "Destination: {V}",
    "Διακομιστής DNS {V}.",
    "Gateway {V}.",
    "Έλεγχος συνδεσιμότητας {V} επιτυχής.",
    "VPN endpoint {V}.",
    "Σύνδεση εξωτερικού πελάτη: {V}, port 443.",
    "[IP] {V}",
    "ip: {V}",
    "host: {V}",
    "Δίκτυο πρόσβασης μέσω {V}.",
]


def _gen_ip_record(rng: random.Random) -> dict:
    frame = rng.choice(_IP_FRAMES)
    v = gen_ip(rng)
    text = frame.replace("{V}", v)
    idx = text.find(v)
    return {
        "text": text,
        "label": [{"category": "ip_address", "start": idx, "end": idx + len(v)}],
        "info": {"source": "v2_10_recall_pack", "domain": "ip_recall"},
    }


# ─── Top-level mixer (weighted by current weakness) ─────────────────

_GENERATORS = [
    ("ama",       _gen_ama_record,   0.25),  # worst class — most weight
    ("amka",      _gen_amka_record,  0.20),
    ("afm",       _gen_afm_record,   0.15),
    ("gemi",      _gen_gemi_record,  0.15),
    ("dl",        _gen_dl_record,    0.13),
    ("ip",        _gen_ip_record,    0.12),
]


def _pick_generator(rng: random.Random):
    r = rng.random()
    cum = 0.0
    for name, fn, w in _GENERATORS:
        cum += w
        if r < cum:
            return name, fn
    return _GENERATORS[-1][0], _GENERATORS[-1][1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=14000)
    parser.add_argument("--seed", type=int, default=2030)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    counts: dict[str, int] = {n: 0 for n, _, _ in _GENERATORS}
    with open(args.output, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            name, fn = _pick_generator(rng)
            try:
                rec = fn(rng)
            except Exception:
                skipped += 1
                continue
            ok = True
            for lab in rec["label"]:
                seg = rec["text"][lab["start"]:lab["end"]]
                if not seg or len(seg) == 0:
                    ok = False
                    break
            if not ok:
                skipped += 1
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
            counts[name] += 1
    print(f"Wrote {written} v2.10-recall records to {args.output} (skipped {skipped})")
    print("Per-class:", json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
