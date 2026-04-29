"""Generate v2.7 targeted weakness pack.

Targets the v2.6 OOD-benchmark residuals (Scenario B aim, F1 ~0.93):
  - secret           0.700 (B=2, C=1)   → boundary-trim + disambig
  - ip_address       0.741 (M=6, H=1)   → narrative / log-context recall
  - pcn              0.818 (C=2)        → explicit ΠΑΠ/PCN marker reinforcement
  - private_person   0.686 (M=51, B=8)  → rare / foreign / hyphenated names + non-name distractors
  - driver_license   0.417 (C=7 vs adt) → strong δίπλωμα-οδήγησης anchoring
  - private_address  0.613 (B=10)       → structured addresses with clean boundaries

Each record is OPF-format JSONL with `text`, `label[{category,start,end}]`,
`info{source, domain}`. Span boundaries verified per record.

Usage:
    python scripts/data_packs/generate_v2_7_targeted_pack.py \\
        --output data/processed/v2_7_targeted_pack.jsonl \\
        --count 12000 --seed 2027
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

from generate_tier1_records import (
    gen_ip_address,
    gen_pcn,
    gen_driver_license as _gen_dl_tier1,
    GREEK_PLATE_LETTERS,
)
from greek_names import compose_name, MALE_FIRST_NAMES, FEMALE_FIRST_NAMES


# ─── Subgenerator 1: secret-boundary ────────────────────────────────

_SECRET_PREFIXES = [
    "tk_live_", "tk_test_", "gpat_", "ghs_", "AKIA", "ASIA",
    "tok_", "key_", "whsec_", "xoxb-", "xoxp-",
    "Bearer ", "ya29.", "EAA", "",
]

_SECRET_ALPHABET = string.ascii_letters + string.digits + "_-"


def _gen_secret_value(rng: random.Random) -> str:
    n = rng.choice([20, 24, 28, 32, 36, 40, 48, 56, 64])
    prefix = rng.choice(_SECRET_PREFIXES)
    body = "".join(rng.choices(_SECRET_ALPHABET, k=n))
    return prefix + body


# Boundary-stress templates: each emits text + the secret value.
# Goal — teach: trailing punctuation, closing quotes, brackets, commas
# are NOT part of the secret span.
_SECRET_FRAMES = [
    # Quoted — span excludes quotes
    ('Authorization: "{S}"', '"', '"'),
    ("api_key='{S}'", "'", "'"),
    ('config["secret"] = "{S}";', '"', '";'),
    ("os.environ['SECRET'] = '{S}'", "'", "'"),
    # Trailing punctuation
    ("Κωδικός: {S}.", "", "."),
    ("Token: {S}!", "", "!"),
    ("API_KEY={S},", "", ","),
    ("secret={S};", "", ";"),
    ("Παρακαλώ φυλάξτε τον κωδικό {S}.", "", "."),
    # Brackets / parens
    ("[token={S}]", "", "]"),
    ("(secret: {S})", "", ")"),
    ("<X-Auth-Token: {S}>", "", ">"),
    # Multi-line / log context
    ("DEBUG  auth.py:42  loaded SECRET={S}\nINFO   server up", "", "\n"),
    ("2026-04-29T12:00:00Z token={S} client=10.0.0.1", "", " "),
    # Inline punctuation
    ("Bearer {S} -- δοκιμή", "", " --"),
    ("Header: Authorization=Bearer {S}\r\nContent-Type: json", "", "\r\n"),
    # JSON / YAML
    ('{{"api_key":"{S}","env":"prod"}}', '"', '"'),
    ("api_key: {S}\nenv: prod", "", "\n"),
    # Disambig — secret near similar-looking token (which should NOT be labelled)
    ("Παλαιός κωδικός 1234, νέος SECRET={S}.", "", "."),
    ("user_id=42, token={S}, session=abc", "", ","),
]


def _gen_secret_record(rng: random.Random) -> dict:
    template, _lq, _rq = rng.choice(_SECRET_FRAMES)
    sec = _gen_secret_value(rng)
    text = template.replace("{S}", sec)
    idx = text.find(sec)
    return {
        "text": text,
        "label": [{"category": "secret", "start": idx, "end": idx + len(sec)}],
        "info": {"source": "v2_7_targeted_pack", "domain": "secret_boundary"},
    }


# ─── Subgenerator 2: ip-narrative ───────────────────────────────────

_IP_FRAMES = [
    "Σύνδεση από {IP} στις 14:23.",
    "Server log: client {IP} requested /api/v1/users.",
    "Ο εξυπηρετητής {IP} επιστρέφει σφάλμα 503.",
    "Ζητήσεις από τη διεύθυνση {IP} αυξήθηκαν.",
    "Firewall block: source={IP}, dest=10.0.0.5",
    "Επιτυχής αυθεντικοποίηση από {IP}.",
    "Η συσκευή με IP {IP} αποσυνδέθηκε.",
    "Διεύθυνση {IP} προστέθηκε στη λίστα αποκλεισμού.",
    "Ζώνη DMZ: εσωτερικός κόμβος {IP} εξωτερικά μη προσβάσιμος.",
    "Ping προς {IP}: 4 packets, 0% loss.",
    "Παρακολούθηση κίνησης από/προς {IP} ενεργή.",
    "Διακομιστής DNS {IP} δεν αποκρίνεται.",
    "Από: 192.168.1.10  Προς: {IP}  Bytes: 4823",
    "Ο πελάτης συνδέθηκε από εξωτερική IP {IP}, port 443.",
    "Σημείωση: η στατική διεύθυνση {IP} ανήκει στον λογιστή.",
    "Tunnel endpoint: {IP}",
    "Επανέλεγχος συνδεσιμότητας στη {IP} απαιτείται.",
    "Καταγραφή: incoming {IP} -- ok",
    "Έλεγχος δικτύου: gateway {IP}, broadcast 192.168.1.255.",
    "VPN client peer={IP} connected.",
    # Multi-IP records
    ("Συνδέσεις: {IP1}, {IP2}.", 2),
    ("Routing: {IP1} -> {IP2}.", 2),
    ("Πελάτες: {IP1} (login), {IP2} (idle).", 2),
    ("Διπλή πηγή: primary {IP1}, secondary {IP2}.", 2),
]


def _gen_ip_record(rng: random.Random) -> dict:
    item = rng.choice(_IP_FRAMES)
    if isinstance(item, tuple):
        template, n = item
        ips = [gen_ip_address(rng) for _ in range(n)]
        text = template
        for i, ip in enumerate(ips, start=1):
            text = text.replace("{IP" + str(i) + "}", ip)
        labels = []
        cursor = 0
        for ip in ips:
            idx = text.find(ip, cursor)
            labels.append({"category": "ip_address", "start": idx, "end": idx + len(ip)})
            cursor = idx + len(ip)
    else:
        ip = gen_ip_address(rng)
        text = item.replace("{IP}", ip)
        idx = text.find(ip)
        labels = [{"category": "ip_address", "start": idx, "end": idx + len(ip)}]
    return {
        "text": text,
        "label": labels,
        "info": {"source": "v2_7_targeted_pack", "domain": "ip_narrative"},
    }


# ─── Subgenerator 3: pcn-explicit ───────────────────────────────────

_PCN_FRAMES = [
    "Προσωπικός Αριθμός Πολίτη: {PCN}",
    "Π.Α.Π. {PCN}",
    "ΠΑΠ: {PCN}",
    "PCN: {PCN}",
    "Personal Citizen Number {PCN}",
    "Νέος ΠΑΠ πολίτη {PCN} καταχωρήθηκε.",
    "Καταχώρηση Π.Α.Π. {PCN} στο μητρώο.",
    "Ο πολίτης με ΠΑΠ {PCN} αιτείται ανανέωση.",
    "ΠΑΠ {PCN} -- επιτυχής επαλήθευση.",
    "Επαλήθευση Personal Citizen Number {PCN} από κρατική υπηρεσία.",
    "Στοιχεία ταυτοποίησης πολίτη: ΠΑΠ {PCN}.",
    "Προσωπικός Αριθμός Πολίτη {PCN} | έκδοση 2025",
    "Έγγραφο εκδόθηκε με Π.Α.Π.: {PCN}.",
    "Πιστοποιητικό συνδεδεμένο με PCN {PCN}.",
    "Κάρτα Πολίτη ΠΑΠ {PCN} ενεργή.",
    "[ΠΑΠ {PCN}]",
    "ΠΑΠ:{PCN}",
    "PAP={PCN}",
]


def _gen_pcn_record(rng: random.Random) -> dict:
    template = rng.choice(_PCN_FRAMES)
    pcn = gen_pcn(rng)
    text = template.replace("{PCN}", pcn)
    idx = text.find(pcn)
    return {
        "text": text,
        "label": [{"category": "pcn", "start": idx, "end": idx + len(pcn)}],
        "info": {"source": "v2_7_targeted_pack", "domain": "pcn_explicit"},
    }


# ─── Subgenerator 4: person-rare ────────────────────────────────────

# Foreign names in Greek transliteration — common in real-world Greek text.
_FOREIGN_NAMES = [
    "Σμιθ", "Μύλλερ", "Καν", "Γιοχάνσον", "Σβένσον", "Καρλσον",
    "Ντι Ματτέο", "Φερνάντες", "Γκαρσία", "Κούπερ", "Μάιερ",
    "Ντε Λα Πένα", "Ο'Κόνορ", "Μακ Ντόναλντ", "Βαν Ντερ Μπεργκ",
    "Σαντοβάλ", "Ροντρίγκες", "Καστίλιο", "Ναβαρρέτε",
    "Λι", "Γουάνγκ", "Ζανγκ", "Καρμπόνε", "Ντελίτο",
    "Ζακαρία", "Χαλίντ", "Νουρ", "Σαλάχ", "Ομάρ",
    "Ντουμπρόφσκι", "Νοβάκοβιτς", "Πέτροβιτς",
]

_FOREIGN_FIRST = [
    "Τζων", "Μάικλ", "Νταβίντ", "Κρις", "Πέτερ", "Φραντς",
    "Άννα", "Μαρία", "Έλενα", "Σόφι", "Ίνγκριντ",
    "Λούκας", "Τόμας", "Άνταμ", "Ίαν",
    "Σάρα", "Ρέιτσελ", "Λίλι", "Μαντλέν",
]

# Compound / hyphenated Greek surnames
_HYPHENATED_SURNAMES = [
    "Παπαδόπουλος-Λάμπρου", "Νικολαΐδης-Σταυρόπουλος",
    "Καραντώνη-Ζαχαρίου", "Δημητρίου-Παπαδάκης",
    "Σταματίου-Χατζηγιάννη", "Θεοδωρίδου-Πέτρου",
]

# Capitalized non-name distractors — should NOT be labelled. Inserted
# alongside a real name to teach the model to ignore them.
_NON_NAME_CAPITALIZED = [
    "Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο", "Λάρισα",
    "Microsoft", "Google", "Amazon", "Uber", "Netflix",
    "Πανεπιστήμιο", "Υπουργείο", "Δήμος", "Περιφέρεια",
    "Δευτέρα", "Τρίτη", "Ιανουάριος", "Φεβρουάριος",
    "ΟΤΕ", "ΔΕΗ", "ΕΛΤΑ", "ΟΣΕ", "ΟΑΕΔ",
]


def _gen_foreign_name(rng: random.Random) -> str:
    if rng.random() < 0.6:
        return rng.choice(_FOREIGN_FIRST) + " " + rng.choice(_FOREIGN_NAMES)
    return rng.choice(_FOREIGN_NAMES)


def _gen_hyphenated_name(rng: random.Random) -> str:
    pool = MALE_FIRST_NAMES + FEMALE_FIRST_NAMES
    return rng.choice(pool) + " " + rng.choice(_HYPHENATED_SURNAMES)


_PERSON_FRAMES = [
    "Ο/Η {NAME} υπέγραψε το έγγραφο.",
    "Με την παρούσα, ο/η {NAME} εκπροσωπεί την εταιρεία.",
    "Παρών/-ούσα: {NAME}.",
    "Από: {NAME}",
    "Προς: {NAME}",
    "Συντάκτης: {NAME}",
    "Συμμετέχοντες — {NAME}, παρατηρητής.",
    "Ο/Η {NAME} ορίστηκε ως υπεύθυνος.",
    "Δηλώσεις του/της {NAME}: \"σχολιάζω αύριο\".",
    "Εκπρόσωπος: {NAME}.",
    "Ομιλητής: {NAME}.",
    "Παραλήπτης: {NAME}",
    "Με εκτίμηση,\n{NAME}",
    "Ευχαριστούμε τον/την {NAME} για τη συμμετοχή.",
    "Η ομάδα: {NAME}.",
    "Καλεσμένος της εκδήλωσης: {NAME}.",
    "Σύμβουλος: {NAME}",
    "Επιβλέπων: {NAME}",
    # With distractors
    "Ο/Η {NAME} ταξίδεψε από την {DISTRACT} στη Λάρισα.",
    "Η αναφορά του/της {NAME} αφορά τη {DISTRACT}.",
    "Ο/Η {NAME} εργάζεται στη {DISTRACT}.",
    "Σύμφωνα με τον/την {NAME}, η {DISTRACT} ανακοίνωσε αλλαγές.",
    "Ο/Η {NAME} επισκέφθηκε το {DISTRACT} χθες.",
]


def _gen_person_record(rng: random.Random) -> dict:
    template = rng.choice(_PERSON_FRAMES)
    roll = rng.random()
    if roll < 0.30:
        # Foreign name
        name_text = _gen_foreign_name(rng)
    elif roll < 0.45:
        # Hyphenated Greek
        name_text = _gen_hyphenated_name(rng)
    elif roll < 0.55:
        # First-only (no surname)
        n = compose_name(rng, first_only=True)
        name_text = n.text
    elif roll < 0.62:
        # Last-only
        n = compose_name(rng, last_only=True)
        name_text = n.text
    elif roll < 0.72:
        # Last-first order
        n = compose_name(rng, last_first_order=True)
        name_text = n.text
    else:
        # Standard
        n = compose_name(rng)
        name_text = n.text
    text = template.replace("{NAME}", name_text)
    if "{DISTRACT}" in text:
        text = text.replace("{DISTRACT}", rng.choice(_NON_NAME_CAPITALIZED))
    idx = text.find(name_text)
    return {
        "text": text,
        "label": [{"category": "private_person", "start": idx, "end": idx + len(name_text)}],
        "info": {"source": "v2_7_targeted_pack", "domain": "person_rare"},
    }


# ─── Subgenerator 5: dl-vs-adt strong anchoring ─────────────────────

_DL_FRAMES = [
    "Δίπλωμα οδήγησης κατηγορίας Β: {DL}",
    "Ο/Η οδηγός κατέχει δίπλωμα οδήγησης {DL}.",
    "Αρ. διπλώματος οδήγησης: {DL}",
    "Δίπλωμα οδήγησης (Β/Γ/Δ) {DL}, ισχύει έως 2030.",
    "Άδεια οδήγησης {DL} εκδοθείσα από Διεύθυνση Μεταφορών.",
    "Driving Licence No. {DL}",
    "Παρουσίαση διπλώματος οδήγησης αρ. {DL} κατά τον έλεγχο.",
    "Δίπλωμα: {DL} | κατηγορία ΒΕ",
    "Ανανέωση διπλώματος οδήγησης {DL} ολοκληρώθηκε.",
    "Στοιχεία οδηγού — δίπλωμα οδήγησης {DL}.",
    "Πληροφορίες οχήματος: ο οδηγός με δίπλωμα {DL} βρισκόταν εν υπηρεσία.",
    "Άδεια οδ. αρ. {DL} εκδ. 2024.",
    "Driver licence number: {DL}",
    "Δίπλωμα οδήγησης #{DL}",
    "Επαγγελματικό δίπλωμα οδήγησης {DL}, κατηγορία Γ.",
    "Πιστοποιητικό ικανότητας οδηγού — δίπλωμα {DL}.",
    "Διοικητική κύρωση: αφαίρεση διπλώματος οδήγησης {DL} για 30 ημέρες.",
    "Κρατικό δίπλωμα οδήγησης {DL}",
]


def _gen_dl_value(rng: random.Random) -> str:
    """DL — bias to 9-digit numeric since that's the canonical Greek form."""
    if rng.random() < 0.85:
        return "".join(rng.choices(string.digits, k=9))
    # Greek-letter + digits variant
    letters = "".join(rng.choices(GREEK_PLATE_LETTERS, k=2))
    digits = "".join(rng.choices(string.digits, k=6))
    return f"{letters}-{digits}"


def _gen_dl_record(rng: random.Random) -> dict:
    template = rng.choice(_DL_FRAMES)
    dl = _gen_dl_value(rng)
    text = template.replace("{DL}", dl)
    idx = text.find(dl)
    return {
        "text": text,
        "label": [{"category": "driver_license", "start": idx, "end": idx + len(dl)}],
        "info": {"source": "v2_7_targeted_pack", "domain": "dl_strong"},
    }


# ─── Subgenerator 6: address-boundary ───────────────────────────────

_STREETS = [
    "Ερμού", "Σταδίου", "Πανεπιστημίου", "Ακαδημίας", "Πατησίων",
    "Λεωφ. Κηφισίας", "Λεωφ. Συγγρού", "Λεωφ. Αλεξάνδρας", "Λεωφ. Βασ. Σοφίας",
    "Παν. Τσαλδάρη", "Αγ. Παρασκευής", "Ηρώων Πολυτεχνείου",
    "Αγίου Δημητρίου", "Φιλελλήνων", "Μητροπόλεως",
    "Πλατεία Συντάγματος", "Πλατεία Ομονοίας", "Λ. Μεσογείων",
    "Παπαδιαμάντη", "Σολωμού", "Καλβού", "Σικελιανού",
    "25ης Μαρτίου", "28ης Οκτωβρίου", "17ης Νοεμβρίου",
]

_CITIES = [
    "Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο", "Λάρισα", "Βόλος",
    "Ιωάννινα", "Καβάλα", "Χαλκίδα", "Ρόδος", "Καλαμάτα",
    "Μαρούσι", "Χαλάνδρι", "Νέα Σμύρνη", "Καλλιθέα", "Πειραιάς",
    "Γλυφάδα", "Νέο Ψυχικό", "Παλαιό Φάληρο", "Νέα Ιωνία",
]


def _gen_address_value(rng: random.Random) -> str:
    street = rng.choice(_STREETS)
    num = rng.randint(1, 250)
    if rng.random() < 0.3:
        # add letter suffix
        num_str = f"{num}{rng.choice(['Α','Β','Γ','α','β'])}"
    else:
        num_str = str(num)
    tk = rng.randint(10000, 85999)
    city = rng.choice(_CITIES)
    style = rng.random()
    if style < 0.30:
        return f"{street} {num_str}, {tk} {city}"
    elif style < 0.55:
        return f"{street} {num_str}, Τ.Κ. {tk}, {city}"
    elif style < 0.75:
        return f"{street} {num_str}, {city} {tk}"
    elif style < 0.85:
        return f"Οδός {street} {num_str}, {tk} {city}"
    else:
        return f"{street} {num_str}"


_ADDRESS_FRAMES = [
    # Frames that put the address near boundary-stress tokens.
    "Διεύθυνση: {ADDR}.",
    "Στοιχεία αλληλογραφίας — {ADDR}",
    "Αποστολή στη διεύθυνση {ADDR}.",
    "({ADDR})",
    "Έδρα εταιρείας: {ADDR}",
    "Κατοικία: {ADDR}",
    "Από: {ADDR}",
    "Προς: {ADDR}",
    "Παράδοση: {ADDR}.",
    "Διεύθυνση πελάτη {ADDR}, ώρα παράδοσης 14:00.",
    "[Διεύθ.] {ADDR}",
    "Νέα διεύθυνση κατοικίας: {ADDR}.",
    "Ταχ. διεύθυνση: {ADDR}",
    "Σημείο παραλαβής — {ADDR}.",
    "Καταχώρηση διεύθυνσης {ADDR} στο σύστημα.",
    "Διεύθυνση εργασίας {ADDR}, τηλ. εσωτερικό 23.",
    "Παρακαλούμε ενημερώστε εάν η διεύθυνση {ADDR} είναι σωστή.",
    "Φυσική διεύθυνση κατοικίας του ασφαλισμένου: {ADDR}.",
    "Ληξιαρχική πράξη — οικία: {ADDR}.",
    "Εργοστάσιο στη διεύθυνση {ADDR} ξεκίνησε λειτουργία.",
    # Boundary stress — address adjacent to other PII-looking tokens
    "Διεύθυνση {ADDR}, τηλέφωνο 2101234567.",
    "{ADDR}\nΤηλ.: 6912345678",
    "Διεύθυνση: {ADDR}; ΑΦΜ εταιρείας: 123456789.",
]


def _gen_address_record(rng: random.Random) -> dict:
    template = rng.choice(_ADDRESS_FRAMES)
    addr = _gen_address_value(rng)
    text = template.replace("{ADDR}", addr)
    idx = text.find(addr)
    return {
        "text": text,
        "label": [{"category": "private_address", "start": idx, "end": idx + len(addr)}],
        "info": {"source": "v2_7_targeted_pack", "domain": "address_boundary"},
    }


# ─── Top-level mixer ────────────────────────────────────────────────

_GENERATORS = [
    ("secret",          _gen_secret_record,  0.10),
    ("ip_address",      _gen_ip_record,      0.10),
    ("pcn",             _gen_pcn_record,     0.08),
    ("private_person",  _gen_person_record,  0.40),
    ("driver_license",  _gen_dl_record,      0.16),
    ("private_address", _gen_address_record, 0.16),
]


def _pick_generator(rng: random.Random):
    r = rng.random()
    cum = 0.0
    for name, fn, w in _GENERATORS:
        cum += w
        if r < cum:
            return name, fn
    return _GENERATORS[-1][0], _GENERATORS[-1][1]


def generate_record(rng: random.Random) -> dict:
    _, fn = _pick_generator(rng)
    return fn(rng)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=2027)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    counts: dict[str, int] = {n: 0 for n, _, _ in _GENERATORS}
    with open(args.output, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            name, fn = _pick_generator(rng)
            rec = fn(rng)
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
    print(f"Wrote {written} v2.7-targeted records to {args.output} (skipped {skipped})")
    print("Per-class:", json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
