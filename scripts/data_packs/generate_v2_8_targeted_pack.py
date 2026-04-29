"""Generate v2.8 root-cause-driven pack.

v2.7 OOD-benchmark triage exposed precise failure modes. Each sub-pack
targets one diagnosed gap. Goal: lift F1 0.814 → 0.86-0.89.

Sub-packs:
  1. person-vocative-title    — "κ./κα/Δρ./Αξιότιμη + SURNAME-only" (vocative case)
  2. person-foreign-latin     — Latin-script foreign names embedded in Greek text
  3. person-dense-pii         — names inside multi-PII forms (5+ adjacent PII)
  4. address-multi            — "από X προς Y" / "από X σε Y" relocation patterns
  5. address-polytonic        — polytonic-script addresses (Ἀκαδημίας, Ἀθῆναι)
  6. address-short            — street+num only (no city/ZIP) gold short spans
  7. address-negative         — text containing dates/amounts/rooms/meds with NO
                                 address (label list empty for address class) —
                                 teaches model what is NOT an address
  8. secret-password          — password-style values with special chars
                                 (#$!&@?) + Greek "Κωδ. πρόσβασης:" markers

Usage:
    python scripts/data_packs/generate_v2_8_targeted_pack.py \\
        --output data/processed/v2_8_targeted_pack.jsonl \\
        --count 14000 --seed 2028
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

from greek_names import (
    compose_name,
    inflect_surname,
    inflect_first_name,
    SURNAMES_M,
    SURNAMES_F,
    MALE_FIRST_NAMES,
    FEMALE_FIRST_NAMES,
)


# ─── Subgenerator 1: vocative-title (FIX person-miss pattern A) ─────

_TITLE_VOC_M = ["Κύριε", "κ.", "Αξιότιμε κ.", "Αγαπητέ κ.", "Δρ.", "Καθηγητή", "Αξιότιμε"]
_TITLE_VOC_F = ["Κυρία", "κα.", "κα", "Αξιότιμη κα", "Αγαπητή κα", "Δρ.", "Καθηγήτρια", "Αξιότιμη"]

_VOC_FRAMES = [
    "{TITLE} {SURNAME},\n\nΣας ενημερώνουμε ότι η αίτησή σας παρελήφθη.",
    "Αξιότιμε {SURNAME}, παρακαλούμε επιβεβαιώστε τα στοιχεία σας.",
    "{TITLE} {SURNAME}, η συμβολή σας ήταν καθοριστική.",
    "Αγαπητέ {SURNAME}, ευχαριστούμε για τη συμμετοχή.",
    "Καλημέρα {TITLE} {SURNAME}, η συνάντηση μεταφέρθηκε για την Πέμπτη.",
    "{TITLE} {SURNAME}, η εκδήλωση πραγματοποιείται την Παρασκευή.",
    "Αξιότιμη {SURNAME}, παρακαλώ προσέλθετε στη Διεύθυνση Φορολογίας.",
    "Με την παρούσα ενημερώνεται ο/η {TITLE} {SURNAME}.",
    "Αγαπητέ μας {SURNAME}, σας ευχαριστούμε θερμά.",
    "{TITLE} {SURNAME}, εκκρεμεί η υπογραφή σας.",
]

_FIRSTNAME_VOC_FRAMES = [
    "Γεια {FIRST}! Στείλε μου το ΑΦΜ σου παρακαλώ.",
    "{FIRST} μου, χρειάζομαι τα στοιχεία σου άμεσα.",
    "Καλησπέρα {FIRST}, μπορείς να καλέσεις;",
    "Έλα {FIRST}, πες μου πότε μπορούμε.",
    "{FIRST}, σου άφησα μήνυμα στο τηλέφωνο.",
    "Δες αυτό {FIRST} και πες μου γνώμη.",
    "Ευχαριστώ {FIRST}, τα έλαβα.",
]


def _gen_voc_record(rng: random.Random) -> dict:
    """Vocative title + SURNAME-only OR vocative first-name SMS."""
    style = rng.random()
    if style < 0.65:
        # Title + surname (vocative)
        gender = rng.choice(["m", "f"])
        title_pool = _TITLE_VOC_M if gender == "m" else _TITLE_VOC_F
        title = rng.choice(title_pool)
        surname_root = rng.choice(SURNAMES_M if gender == "m" else SURNAMES_F)
        surname_forms = inflect_surname(surname_root, gender)
        surname = surname_forms["voc"]
        template = rng.choice(_VOC_FRAMES)
        text = template.replace("{TITLE}", title).replace("{SURNAME}", surname)
        idx = text.find(surname)
        if idx == -1:
            return _gen_voc_record(rng)
        labels = [{"category": "private_person", "start": idx, "end": idx + len(surname)}]
    else:
        # First-name vocative SMS
        gender = rng.choice(["m", "f"])
        first_pool = MALE_FIRST_NAMES if gender == "m" else FEMALE_FIRST_NAMES
        first_root = rng.choice(first_pool)
        first_forms = inflect_first_name(first_root, gender)
        first = first_forms["voc"]
        template = rng.choice(_FIRSTNAME_VOC_FRAMES)
        text = template.replace("{FIRST}", first)
        idx = text.find(first)
        if idx == -1:
            return _gen_voc_record(rng)
        labels = [{"category": "private_person", "start": idx, "end": idx + len(first)}]
    return {
        "text": text,
        "label": labels,
        "info": {"source": "v2_8_targeted_pack", "domain": "person_vocative_title"},
    }


# ─── Subgenerator 2: foreign-latin (FIX person-miss pattern B) ──────

_FOREIGN_FIRST_LATIN = [
    "John", "Michael", "David", "Chris", "Peter", "Frank",
    "Anna", "Maria", "Helena", "Sophie", "Ingrid", "Sarah",
    "Lukas", "Thomas", "Adam", "Ian", "Rachel", "Lily",
    "Hans", "Klaus", "Carlos", "Miguel", "Luis",
    "Yuki", "Hiroshi", "Wei", "Liu",
]

_FOREIGN_LAST_LATIN = [
    "Smith", "Jones", "Müller", "Schmidt", "Khan", "Singh",
    "Petridi", "Petridis", "Karagiannis", "Christou",
    "Rodriguez", "Garcia", "Fernandez", "Sanchez",
    "Johnson", "Williams", "Brown", "Davis",
    "O'Connor", "Van Der Berg", "Di Mateo", "De La Cruz",
    "Tanaka", "Kim", "Park", "Wang",
]

_LATIN_NAME_FRAMES = [
    "Επιβάτης {NAME}, διαβατήριο AΓ7654321.",
    "Check-in: {NAME}, δωμάτιο 412.",
    "Στοιχεία ξένου ασθενούς: {NAME}.",
    "Καλεσμένος της εκδήλωσης: {NAME}.",
    "Ο πελάτης {NAME} αιτήθηκε αλλαγή.",
    "Από: {NAME}",
    "To: {NAME}",
    "Συμμετέχων: {NAME}.",
    "Ο/Η {NAME} είναι ξένος υπήκοος.",
    "Ονοματεπώνυμο (αγγλικά): {NAME}.",
    "Ξενοδοχείο Athens Plaza — επώνυμο: {NAME}.",
    "Border control log: passenger {NAME}, εθνικότητα ξένος.",
    "Εκπρόσωπος ξένης εταιρείας: {NAME}.",
]


def _gen_foreign_latin_record(rng: random.Random) -> dict:
    first = rng.choice(_FOREIGN_FIRST_LATIN)
    last = rng.choice(_FOREIGN_LAST_LATIN)
    name = f"{first} {last}"
    template = rng.choice(_LATIN_NAME_FRAMES)
    text = template.replace("{NAME}", name)
    idx = text.find(name)
    return {
        "text": text,
        "label": [{"category": "private_person", "start": idx, "end": idx + len(name)}],
        "info": {"source": "v2_8_targeted_pack", "domain": "person_foreign_latin"},
    }


# ─── Subgenerator 3: dense-PII forms (FIX person-miss pattern F) ────

def _gen_afm(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=9))


def _gen_amka(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=11))


def _gen_adt(rng: random.Random) -> str:
    letters = "".join(rng.choices("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", k=2))
    digits = "".join(rng.choices(string.digits, k=6))
    return f"{letters}-{digits}"


def _gen_phone(rng: random.Random) -> str:
    if rng.random() < 0.6:
        return "69" + "".join(rng.choices(string.digits, k=8))
    return "210" + "".join(rng.choices(string.digits, k=7))


def _gen_dl_value(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=9))


_DENSE_FRAMES = [
    # Each frame has {NAME} + several other PII slots filled separately
    "Στοιχεία αίτησης: Ονομ. {NAME} | ΑΦΜ {AFM} | ΑΜΚΑ {AMKA} | ΑΔΤ {ADT}.",
    "Δικαιούχος: {NAME}, ΑΦΜ {AFM}, ΑΜΚΑ {AMKA}, τηλ. {PHONE}.",
    "Ασθενής: {NAME}, ΑΜΚΑ {AMKA}, ηλικίας 50 ετών.",
    "Συνταγή για: {NAME}, ΑΜΚΑ {AMKA}.",
    "Ιδιοκτήτης {NAME}, ΑΦΜ {AFM}.",
    "Κάτοχος: {NAME}. Αρ. διπλώματος: {DL}. ΑΦΜ: {AFM}.",
    "Ανανέωση βιβλιαρίου ΙΚΑ. Δικαιούχος: {NAME}. ΑΜΑ ΙΚΑ: 4567823. ΑΜΚΑ: {AMKA}.",
    "Παράβαση Κ.Ο.Κ.: όχημα ΙΚΤ-4567, οδηγός {NAME}, ΑΔΤ {ADT}. Πρόστιμο 200€.",
    "Αξιότιμη κα {NAME}, εκκρεμεί η δήλωση Ε1. ΑΦΜ {AFM}, ΑΔΤ {ADT}, ΑΜΚΑ {AMKA}.",
    "Αίτηση έκδοσης διαβατηρίου. Στοιχεία: {NAME}, διαβατήριο AΒ4567321.",
    "Ραντεβού 15:30, Δρ. {NAME}. ΑΜΚΑ {AMKA}.",
    "Ονομ. {NAME} — ΑΦΜ {AFM} — ΑΜΚΑ {AMKA} — Τηλ. {PHONE}.",
    "Φόρος ακίνητης περιουσίας. Ιδιοκτήτης {NAME}, ΑΦΜ {AFM}. Ποσό: 487€.",
    "Πελάτης: {NAME}, email kpapas@firm.gr, 6951234876.",
    "Συμβαλλόμενος: {NAME} (ΑΦΜ {AFM}). Δίπλωμα οδήγησης {DL}.",
]


def _gen_dense_pii_record(rng: random.Random) -> dict:
    template = rng.choice(_DENSE_FRAMES)
    n = compose_name(rng)
    name_text = n.text
    text = template.replace("{NAME}", name_text)
    text = (text
            .replace("{AFM}", _gen_afm(rng))
            .replace("{AMKA}", _gen_amka(rng))
            .replace("{ADT}", _gen_adt(rng))
            .replace("{PHONE}", _gen_phone(rng))
            .replace("{DL}", _gen_dl_value(rng)))
    idx = text.find(name_text)
    if idx == -1:
        return _gen_dense_pii_record(rng)
    return {
        "text": text,
        "label": [{"category": "private_person", "start": idx, "end": idx + len(name_text)}],
        "info": {"source": "v2_8_targeted_pack", "domain": "person_dense_pii"},
    }


# ─── Subgenerator 4: multi-address (FIX address boundary merge) ─────

_STREETS = [
    "Ερμού", "Σταδίου", "Πανεπιστημίου", "Ακαδημίας", "Πατησίων",
    "Κηφισίας", "Συγγρού", "Αλεξάνδρας", "Βασ. Σοφίας",
    "Παν. Τσαλδάρη", "Αγ. Παρασκευής", "Ηρώων Πολυτεχνείου",
    "Φιλελλήνων", "Μητροπόλεως", "Σολωμού", "Καλβού", "Σικελιανού",
    "25ης Μαρτίου", "28ης Οκτωβρίου", "17ης Νοεμβρίου",
    "Σκουφά", "Δοϊράνης", "Νίκης", "Σεβαστουπόλεως",
    "Ηπείρου", "Ευελπίδων", "Θηβών",
]

_CITIES = [
    "Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο", "Λάρισα",
    "Μαρούσι", "Χαλάνδρι", "Νέα Σμύρνη", "Καλλιθέα", "Πειραιάς",
    "Γλυφάδα", "Νέο Ψυχικό", "Παλαιό Φάληρο", "Νέα Ιωνία",
    "Αμπελόκηποι", "Πετρούπολη", "Κυψέλη",
]


def _gen_addr_full(rng: random.Random) -> str:
    street = rng.choice(_STREETS)
    num = rng.randint(1, 250)
    tk = rng.randint(10000, 85999)
    city = rng.choice(_CITIES)
    style = rng.random()
    if style < 0.5:
        return f"{street} {num}, {tk} {city}"
    elif style < 0.8:
        return f"{street} {num}, {city}"
    else:
        return f"Λεωφ. {street} {num}, {city}"


_MULTI_ADDR_FRAMES = [
    "Παρακαλώ αλλάξτε τη διεύθυνση από {ADDR1} σε {ADDR2}.",
    "Μετακόμιση από {ADDR1} προς {ADDR2}.",
    "Διεύθυνση επικοινωνίας μεταβλήθηκε: {ADDR1} → {ADDR2}.",
    "Παλαιά κατοικία: {ADDR1}. Νέα κατοικία: {ADDR2}.",
    "Αποστολή από {ADDR1} προς {ADDR2}.",
    "Από {ADDR1} σε {ADDR2}, μέσω εταιρείας μετακομίσεων.",
]


def _gen_multi_addr_record(rng: random.Random) -> dict:
    template = rng.choice(_MULTI_ADDR_FRAMES)
    a1 = _gen_addr_full(rng)
    a2 = _gen_addr_full(rng)
    while a2 == a1:
        a2 = _gen_addr_full(rng)
    text = template.replace("{ADDR1}", a1).replace("{ADDR2}", a2)
    i1 = text.find(a1)
    i2 = text.find(a2, i1 + len(a1))
    return {
        "text": text,
        "label": [
            {"category": "private_address", "start": i1, "end": i1 + len(a1)},
            {"category": "private_address", "start": i2, "end": i2 + len(a2)},
        ],
        "info": {"source": "v2_8_targeted_pack", "domain": "address_multi"},
    }


# ─── Subgenerator 5: polytonic addresses ────────────────────────────

_POLY_STREETS = [
    "Ἀκαδημίας", "Πανεπιστημίου", "Σταδίου", "Ἑρμοῦ", "Ἀθηνᾶς",
    "Πατησίων", "Ἁγίου Δημητρίου", "Φιλελλήνων", "Σόλωνος",
    "Σκουφᾶ", "Ἰπποκράτους", "Νίκης", "Μητροπόλεως",
]

_POLY_CITIES = ["Ἀθῆναι", "Ἀθήναις", "Θεσσαλονίκη", "Πειραιεύς", "Πάτραι"]


def _gen_poly_addr(rng: random.Random) -> str:
    """Return address VALUE only (no οδοῦ/ὁδοῦ prefix). Carrier handles prefix."""
    street = rng.choice(_POLY_STREETS)
    num = rng.randint(1, 99)
    if rng.random() < 0.5:
        return f"{street} {num}"
    city = rng.choice(_POLY_CITIES)
    return f"{street} {num}, {city}"


_POLY_FRAMES = [
    "Πρὸς τὸν κύριον {NAME}, διαμένοντα ἐπὶ τῆς ὁδοῦ {ADDR}.",
    "Διαμένει ἐπὶ τῆς {ADDR}.",
    "Ἡ ἕδρα τῆς ἑταιρείας εἶναι ἐπὶ τῆς {ADDR}.",
    "Ταχ. διεύθυνσις: {ADDR}.",
    "Διεύθυνσις κατοικίας: {ADDR}.",
    "Ἀποστέλλεται εἰς {ADDR}.",
    "Ἐπὶ τῆς {ADDR} εὑρίσκεται τὸ γραφεῖον.",
]


def _gen_poly_addr_record(rng: random.Random) -> dict:
    template = rng.choice(_POLY_FRAMES)
    addr = _gen_poly_addr(rng)
    if "{NAME}" in template:
        n = compose_name(rng)
        # Strip name span — just fill in, only label address
        text = template.replace("{NAME}", n.text).replace("{ADDR}", addr)
    else:
        text = template.replace("{ADDR}", addr)
    idx = text.find(addr)
    labels = [{"category": "private_address", "start": idx, "end": idx + len(addr)}]
    if "{NAME}" not in template:
        pass
    else:
        # Also label the name we substituted
        ni = text.find(n.text)
        if ni != -1 and ni != idx:
            labels.append({"category": "private_person", "start": ni, "end": ni + len(n.text)})
    labels.sort(key=lambda L: L["start"])
    return {
        "text": text,
        "label": labels,
        "info": {"source": "v2_8_targeted_pack", "domain": "address_polytonic"},
    }


# ─── Subgenerator 6: short-only addresses ───────────────────────────

_SHORT_FRAMES = [
    "Διατηρεῖ ἰατρεῖο ἐπὶ τῆς ὁδοῦ {ADDR}.",
    "Διατηρεί ιατρείο επί της οδού {ADDR}.",
    "Στη διεύθυνση {ADDR}.",
    "Επί της οδού {ADDR}.",
    "Επιχείρηση επί της {ADDR}.",
    "Παράρτημα στην οδό {ADDR}.",
    "Σήμα στην {ADDR}.",
    "Ξενοδοχείο στην {ADDR}.",
    "Συνεργείο επί της οδού {ADDR}.",
    "Εργαστήριο στη διεύθυνση {ADDR}.",
]


def _gen_short_addr(rng: random.Random) -> str:
    street = rng.choice(_STREETS)
    num = rng.randint(1, 99)
    return f"{street} {num}"


def _gen_short_addr_record(rng: random.Random) -> dict:
    template = rng.choice(_SHORT_FRAMES)
    addr = _gen_short_addr(rng)
    text = template.replace("{ADDR}", addr)
    idx = text.find(addr)
    return {
        "text": text,
        "label": [{"category": "private_address", "start": idx, "end": idx + len(addr)}],
        "info": {"source": "v2_8_targeted_pack", "domain": "address_short"},
    }


# ─── Subgenerator 7: address-NEGATIVE (critical fix for halluc) ─────

_GREEK_MONTHS = [
    "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου",
    "Μαΐου", "Ιουνίου", "Ιουλίου", "Αυγούστου",
    "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
]

_MEDICATIONS = [
    "Atorvastatin 20mg", "Paracetamol 500mg", "Amoxicillin 250mg",
    "Aspirin 100mg", "Lisinopril 10mg", "Metformin 850mg",
    "Omeprazole 20mg", "Diazepam 5mg", "Ibuprofen 400mg",
]


def _gen_date_value(rng: random.Random) -> str:
    return f"{rng.randint(1, 28)} {rng.choice(_GREEK_MONTHS)} {rng.randint(1950, 2026)}"


def _gen_amount(rng: random.Random) -> str:
    return f"{rng.randint(10, 99999)},{rng.randint(0, 99):02d}€"


def _gen_room(rng: random.Random) -> str:
    return f"Δωμάτιο {rng.randint(100, 999)}"


def _gen_office(rng: random.Random) -> str:
    return f"Γραφείο {rng.randint(100, 999)}"


# Frames where there is NO address but multiple structured numerics that
# COULD trip the model into hallucinating an address. Every frame MUST
# contain at least one labelable PII slot ({NAME}, {DATE}, {DL}, {AMKA},
# {SURNAME}) so the record is never empty-labelled — otherwise the model
# learns "ignore everything" globally (v2.8 disaster).
_ADDR_NEG_FRAMES = [
    # Birthdate cases (label: name + date)
    "{NAME}, ημερομηνία γέννησης {DATE}, ηλικίας {AGE} ετών.",
    "Ασθενής {NAME}, γεννηθείς/-εῖσα {DATE}.",
    "Ανανέωση διπλώματος αρ. {DL}, κάτοχος {NAME}, ημ. γέννησης {DATE}.",
    "Στοιχεία υπαλλήλου: {NAME}. Πρόσληψη {DATE}.",
    # Medication cases (label: name only)
    "Φάρμακο: {MED}, 1 δισκίο/ημέρα. Επανεξέταση: {DATE}.",
    "Συνταγή: {MED}, ασθενής {NAME}.",
    "Φάρμακο {MED} για ασθενή {NAME}, 2 φορές την ημέρα.",
    # Money cases (label: date)
    "Ποσό προστίμου: {AMOUNT}. Καταβολή έως {DATE}.",
    "Πληρωμή {AMOUNT} στις {DATE}.",
    "Καταβολή ποσού {AMOUNT} από {NAME} ολοκληρώθηκε.",
    # Room/office numbers (label: name)
    "Συνάντηση στο {OFFICE}, ώρες 10-14, παρών ο/η {NAME}.",
    "Check-in επιτυχές. {ROOM}, πελάτης {NAME}, μέχρι αύριο.",
    "Παρακαλώ προσέλθετε στο {OFFICE}, ο/η {NAME} σας περιμένει.",
    "Δωμάτιο {ROOM} ανατέθηκε στον/στην {NAME}.",
    # Just dates with names (common in records)
    "Ραντεβού: {DATE}, ώρα 10:30, ασθενής {NAME}.",
    "Έκδοση: {DATE}, υπεύθυνος {NAME}.",
    "Λήξη ισχύος: {DATE} για κάτοχο {NAME}.",
    "Ημερομηνία υπογραφής συμβολαίου: {DATE} από {NAME}.",
    # Mixed with names
    "{NAME} ταξίδεψε στις {DATE}.",
    "Παράδοση εργασίας: {DATE}, υπεύθυνος {NAME}.",
    "Ραντεβού 15:30 την {DAY} {DATE}, Δρ. {SURNAME}. ΑΜΚΑ {AMKA}.",
]


def _gen_addr_neg_record(rng: random.Random) -> dict:
    """Address-NEGATIVE: text has structured numerics (dates/amounts/rooms)
    BUT no address. Labels the legitimate PII (date, name, dl, amka) so model
    learns 'date is date, not address' — never produces empty-label records.
    """
    template = rng.choice(_ADDR_NEG_FRAMES)
    text = template

    # Substitute placeholders, recording each substituted PII value
    # alongside its label so we can find offsets after all substitutions.
    substituted: list[tuple[str, str]] = []  # (label_category, value_text)

    if "{NAME}" in text:
        n = compose_name(rng)
        text = text.replace("{NAME}", n.text)
        substituted.append(("private_person", n.text))
    if "{SURNAME}" in text:
        gender = rng.choice(["m", "f"])
        sur = rng.choice(SURNAMES_M if gender == "m" else SURNAMES_F)
        sur_voc = inflect_surname(sur, gender)["voc"]
        text = text.replace("{SURNAME}", sur_voc)
        substituted.append(("private_person", sur_voc))
    if "{DATE}" in text:
        date_v = _gen_date_value(rng)
        text = text.replace("{DATE}", date_v)
        substituted.append(("private_date", date_v))
    if "{DL}" in text:
        dl_v = _gen_dl_value(rng)
        text = text.replace("{DL}", dl_v)
        substituted.append(("driver_license", dl_v))
    if "{AMKA}" in text:
        amka_v = _gen_amka(rng)
        text = text.replace("{AMKA}", amka_v)
        substituted.append(("amka", amka_v))
    # Non-PII fillers: substituted but NOT labelled (they are not classes).
    if "{MED}" in text:
        text = text.replace("{MED}", rng.choice(_MEDICATIONS))
    if "{AMOUNT}" in text:
        text = text.replace("{AMOUNT}", _gen_amount(rng))
    if "{ROOM}" in text:
        text = text.replace("{ROOM}", _gen_room(rng))
    if "{OFFICE}" in text:
        text = text.replace("{OFFICE}", _gen_office(rng))
    if "{AGE}" in text:
        text = text.replace("{AGE}", str(rng.randint(20, 85)))
    if "{DAY}" in text:
        text = text.replace("{DAY}", rng.choice(["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή"]))

    # Locate each substituted value's first occurrence and emit a label.
    labels = []
    cursor = 0
    for cat, val in substituted:
        idx = text.find(val, cursor)
        if idx == -1:
            idx = text.find(val)
        if idx == -1:
            continue
        labels.append({"category": cat, "start": idx, "end": idx + len(val)})
        cursor = idx + len(val)
    labels.sort(key=lambda L: L["start"])
    return {
        "text": text,
        "label": labels,
        "info": {"source": "v2_9_targeted_pack", "domain": "address_negative"},
    }


# ─── Subgenerator 8: secret-password (FIX secret special-char miss) ─

_PASSWORD_PREFIXES = [
    "Κωδ. πρόσβασης:", "Νέος κωδικός:", "Κωδικός:",
    "Password:", "passphrase:", "ΚΩΔΙΚΟΣ:",
    "Κωδ. πρόσβασης βάσης δεδομένων:", "DB password:",
    "VPN password:", "SSH passphrase:", "Νέο password:",
    "password=", "passwd=", "pwd:",
]


def _gen_password_value(rng: random.Random) -> str:
    """Password-style with embedded special chars (#$!&@?)."""
    n_segments = rng.choice([2, 3, 4])
    segments = []
    word_pool = [
        "Pass", "Secret", "Admin", "Prod", "Dev", "Greek", "Athens",
        "Postgres", "Mongo", "Redis", "Token", "Auth", "User",
        "Database", "Server", "App", "Local", "Master",
    ]
    for _ in range(n_segments):
        if rng.random() < 0.5:
            segments.append(rng.choice(word_pool))
        else:
            segments.append("".join(rng.choices(string.ascii_letters + string.digits, k=rng.randint(3, 6))))
    seps = ["#", "$", "!", "&", "@", "?", "*", "_", ""]
    out = segments[0]
    for seg in segments[1:]:
        out += rng.choice(seps) + seg
    # Optionally tail special char
    if rng.random() < 0.6:
        out += rng.choice(["!", "#", "$", "@", "?", "*"])
    # Add year
    if rng.random() < 0.7:
        out += str(rng.choice([2024, 2025, 2026, 2027]))
    # Optional digits at end
    if rng.random() < 0.4:
        out += "".join(rng.choices(string.digits, k=rng.randint(2, 5)))
    return out


_PASSWORD_FRAMES = [
    "{PREFIX} {PWD}",
    "{PREFIX} {PWD}. Μην το κοινοποιείτε.",
    "Νέος {PREFIX} {PWD} ορίστηκε.",
    "{PREFIX} {PWD} -- αλλάξτε το άμεσα.",
    "Ορίσετε νέο κωδικό. {PREFIX} {PWD}.",
    "Στοιχεία πρόσβασης. {PREFIX} {PWD}",
    "{PREFIX} {PWD} (μην το αποθηκεύσετε σε plain text).",
    "Παράδοση κωδικού: {PWD}.",
    "Ο νέος κωδικός είναι {PWD}, παρακαλώ φυλάξτε τον.",
    "{PREFIX} {PWD}!",
    "{PREFIX} {PWD}#",
    "Αλλαγή κωδικού. Νέος: {PWD}.",
    "Το credential για prod είναι {PWD}.",
]


def _gen_secret_pwd_record(rng: random.Random) -> dict:
    template = rng.choice(_PASSWORD_FRAMES)
    pwd = _gen_password_value(rng)
    prefix = rng.choice(_PASSWORD_PREFIXES)
    text = template.replace("{PREFIX}", prefix).replace("{PWD}", pwd)
    # Find the FIRST occurrence of pwd that's NOT part of prefix replacement
    idx = text.find(pwd)
    if idx == -1:
        return _gen_secret_pwd_record(rng)
    return {
        "text": text,
        "label": [{"category": "secret", "start": idx, "end": idx + len(pwd)}],
        "info": {"source": "v2_8_targeted_pack", "domain": "secret_password"},
    }


# ─── Top-level mixer ────────────────────────────────────────────────

_GENERATORS = [
    ("person_voc",        _gen_voc_record,           0.22),
    ("person_foreign",    _gen_foreign_latin_record, 0.10),
    ("person_dense",      _gen_dense_pii_record,     0.22),
    ("address_multi",     _gen_multi_addr_record,    0.12),
    ("address_polytonic", _gen_poly_addr_record,     0.07),
    ("address_short",     _gen_short_addr_record,    0.09),
    ("address_negative",  _gen_addr_neg_record,      0.06),
    ("secret_password",   _gen_secret_pwd_record,    0.12),
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
    parser.add_argument("--seed", type=int, default=2028)
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
            except Exception as e:
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
    print(f"Wrote {written} v2.8-targeted records to {args.output} (skipped {skipped})")
    print("Per-class:", json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
