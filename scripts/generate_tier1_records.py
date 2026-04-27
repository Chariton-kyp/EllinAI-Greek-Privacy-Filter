"""Deterministic Tier-1 PII record generator.

Produces OPF-format JSONL records for the deterministic-format PII
classes that v1 does not yet cover:

    passport            — 2 capital Latin letters + 7 digits (LL#######)
    license_plate       — 3 capital Greek letters + 4 digits (ΑΒΓ-1234)
    vehicle_vin         — 17 alphanumeric (ISO 3779; excludes I, O, Q)
    gemi                — 12 digits (Greek Business Registry)
    ama                 — 7 or 9 digits (legacy IKA / modern ΕΦΚΑ insurance)
    card_pan            — 13-19 digits with Luhn checksum
    cvv                 — 3 or 4 digits, always inside a card-context record
    imei                — 15 digits with Luhn checksum
    ip_address          — IPv4 dotted-quad or IPv6 hex group
    mac_address         — 6 hex pairs separated by `:` or `-`
    driver_license      — 9 digits (per Microsoft Purview entity definition)
    pcn                 — 12 chars: AFM (9 digits) + 1 capital Latin letter + 2 digits
                          (Personal Citizen Number, rolled out from 2025)

Every record is a JSONL line carrying the upstream OPF schema:
``{text, label[{category, start, end}], info{difficulty, domain, source, strategy}}``.

The script is fully offline: no network, no LLM calls, no carrier
corpus required. Each record is built from a per-class carrier
template plus a deterministically-generated PII value, sampled with
an RNG seeded by ``--seed``. Re-running with the same seed and the
same arguments produces byte-identical output.

The label-prefix mode (no-prefix / Greek-prefix / Greeklish-prefix /
English-prefix) is sampled per record from the four-way mix
documented in the v2 label-schema policy. The default share is
``25 / 35 / 20 / 20`` and can be overridden per class via the
``--prefix-mix`` flag.

The OPF span boundary covers the value only. The label prefix word
("Διαβατήριο", "Passport", "ΓΕΜΗ", etc.) and any whitespace or
punctuation between the prefix and the value are explicitly
excluded from the span, matching the convention enforced by
``scripts/relabel_afm_spans.py`` for AFM in v1.1.

Usage:

    # 1,000 passport records, default prefix mix
    python scripts/generate_tier1_records.py \\
        --classes passport --count 1000 --seed 2024 \\
        --output data/processed/v2/phase_1/passport/raw.jsonl

    # All twelve classes, 500 each, deterministic prefix mix
    python scripts/generate_tier1_records.py \\
        --classes passport license_plate vehicle_vin gemi ama \\
                  card_pan cvv imei ip_address mac_address \\
                  driver_license pcn \\
        --count 500 --seed 2024 \\
        --output data/processed/v2/phase_1/tier1_all.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ─── Per-class value generators ─────────────────────────────────────

# Greek capital letters used on Greek civilian licence plates. The
# Greek civilian-plate alphabet is a 14-letter subset that visually
# overlaps with Latin: Α, Β, Ε, Ζ, Η, Ι, Κ, Μ, Ν, Ο, Ρ, Τ, Υ, Χ.
# Generators that emit the Greek-script form use exactly this set.
GREEK_PLATE_LETTERS = "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"

# Latin alphabet excluding I, O, Q (per ISO 3779 to avoid digit/letter
# confusion in VINs).
VIN_ALPHABET = "ABCDEFGHJKLMNPRSTUVWXYZ"


def luhn_check_digit(digits: str) -> int:
    """Return the Luhn check digit for ``digits`` (which should not
    yet include the check digit)."""
    total = 0
    parity = (len(digits) + 1) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10


def gen_passport(rng: random.Random) -> str:
    letters = "".join(rng.choices(string.ascii_uppercase, k=2))
    digits = "".join(rng.choices(string.digits, k=7))
    return f"{letters}{digits}"


def gen_license_plate(rng: random.Random) -> str:
    letters = "".join(rng.choices(GREEK_PLATE_LETTERS, k=3))
    digits = "".join(rng.choices(string.digits, k=4))
    sep = rng.choice(["-", " ", ""])
    return f"{letters}{sep}{digits}"


def gen_vehicle_vin(rng: random.Random) -> str:
    return "".join(rng.choices(VIN_ALPHABET + string.digits, k=17))


def gen_gemi(rng: random.Random) -> str:
    return "".join(rng.choices(string.digits, k=12))


def gen_ama(rng: random.Random) -> str:
    length = rng.choices([9, 7], weights=[0.8, 0.2])[0]
    return "".join(rng.choices(string.digits, k=length))


def gen_card_pan(rng: random.Random) -> str:
    # 16-digit primary path (Visa/Mastercard/Maestro), plus an
    # occasional 15-digit American Express. All Luhn-valid.
    length = rng.choices([16, 15], weights=[0.85, 0.15])[0]
    body = "".join(rng.choices(string.digits, k=length - 1))
    body += str(luhn_check_digit(body))
    if rng.random() < 0.5:
        # Grouped: 4-4-4-4 (or 4-6-5 for 15-digit Amex)
        if length == 16:
            sep = rng.choice([" ", "-"])
            body = sep.join(body[i : i + 4] for i in range(0, 16, 4))
        else:
            sep = rng.choice([" ", "-"])
            body = f"{body[0:4]}{sep}{body[4:10]}{sep}{body[10:15]}"
    return body


def gen_cvv(rng: random.Random) -> str:
    length = rng.choices([3, 4], weights=[0.8, 0.2])[0]
    return "".join(rng.choices(string.digits, k=length))


def gen_imei(rng: random.Random) -> str:
    body = "".join(rng.choices(string.digits, k=14))
    return body + str(luhn_check_digit(body))


def gen_ip_address(rng: random.Random) -> str:
    if rng.random() < 0.85:
        # IPv4
        return ".".join(str(rng.randint(1, 254)) for _ in range(4))
    # IPv6 (8 groups, full form for simplicity)
    return ":".join(f"{rng.randint(0, 0xFFFF):04x}" for _ in range(8))


def gen_mac_address(rng: random.Random) -> str:
    sep = rng.choice([":", "-"])
    return sep.join(f"{rng.randint(0, 255):02x}" for _ in range(6))


def gen_driver_license(rng: random.Random) -> str:
    # Per Microsoft Purview: 9-digit Greek driving-licence number.
    # Genuine licences may also have an alphanumeric sequence; we
    # model both.
    if rng.random() < 0.8:
        return "".join(rng.choices(string.digits, k=9))
    return "".join(rng.choices(string.ascii_uppercase, k=2)) + "".join(
        rng.choices(string.digits, k=6)
    )


def gen_pcn(rng: random.Random) -> str:
    afm = "".join(rng.choices(string.digits, k=9))
    letter = rng.choice(string.ascii_uppercase)
    suffix = "".join(rng.choices(string.digits, k=2))
    return f"{afm}{letter}{suffix}"


# ─── Per-class prefix tokens ────────────────────────────────────────

# Each entry maps (greek, greeklish, english) prefix-token lists.
PREFIXES: dict[str, dict[str, list[str]]] = {
    "passport": {
        "greek": ["Διαβατήριο", "Αρ. Διαβ.", "Αρ. Διαβατηρίου"],
        "greeklish": ["Diavatirio", "Ar. Diav."],
        "english": ["Passport", "Passport No.", "Passport Number"],
    },
    "license_plate": {
        "greek": ["Πινακίδα", "Πιν.", "Αρ. Κυκλ."],
        "greeklish": ["Pinakida", "Pin."],
        "english": ["Plate", "License Plate", "Reg."],
    },
    "vehicle_vin": {
        "greek": ["Πλαίσιο", "Αρ. Πλαισίου", "Αριθμ. Πλαισίου"],
        "greeklish": ["Plaisio", "Ar. Plaisiou"],
        "english": ["VIN", "Chassis", "Chassis No."],
    },
    "gemi": {
        "greek": ["ΓΕΜΗ", "Γ.Ε.ΜΗ.", "Αρ. ΓΕΜΗ"],
        "greeklish": ["GEMI", "G.E.MI."],
        "english": ["GCR", "Greek Business Registry No."],
    },
    "ama": {
        "greek": ["ΑΜΑ", "Α.Μ.Α.", "Αρ. Μητρ. ΕΦΚΑ", "Αρ. Μητρ. ΙΚΑ"],
        "greeklish": ["AMA", "A.M.A."],
        "english": ["IKA Number", "Old Insurance ID"],
    },
    "card_pan": {
        "greek": ["Αρ. Κάρτας", "Πιστωτική", "Χρεωστική", "Κάρτα"],
        "greeklish": ["Karta", "Ar. Kartas"],
        "english": ["Card", "Card No.", "PAN", "Credit Card", "Debit Card"],
    },
    "cvv": {
        "greek": ["Κωδ. Ασφ.", "Κωδ. Επαλ."],
        "greeklish": ["CVV"],
        "english": ["CVV", "CVC", "CSC", "Security Code"],
    },
    "imei": {
        "greek": ["IMEI", "Σειρ. Συσκευής"],
        "greeklish": ["IMEI"],
        "english": ["IMEI", "Device IMEI"],
    },
    "ip_address": {
        "greek": ["IP", "Διεύθ. IP"],
        "greeklish": ["IP"],
        "english": ["IP", "IPv4", "IPv6", "IP Address"],
    },
    "mac_address": {
        "greek": ["MAC", "Διεύθ. MAC"],
        "greeklish": ["MAC"],
        "english": ["MAC", "MAC Address", "Hardware Addr"],
    },
    "driver_license": {
        "greek": ["Δίπλωμα", "Άδ. Οδήγ.", "Άδεια Οδήγησης", "Αρ. Διπλώματος"],
        "greeklish": ["Adeia Odigisis", "Diploma"],
        "english": ["Driver License", "DL", "Driving Licence"],
    },
    "pcn": {
        "greek": ["Π.Α.Π.", "Προσ. Αρ. Πολίτη", "Προσωπικός Αριθμός Πολίτη"],
        "greeklish": ["PAP", "Prosopikos Arithmos Politi"],
        "english": ["PCN", "Personal Citizen Number"],
    },
}

VALUE_GENERATORS: dict[str, Callable[[random.Random], str]] = {
    "passport": gen_passport,
    "license_plate": gen_license_plate,
    "vehicle_vin": gen_vehicle_vin,
    "gemi": gen_gemi,
    "ama": gen_ama,
    "card_pan": gen_card_pan,
    "cvv": gen_cvv,
    "imei": gen_imei,
    "ip_address": gen_ip_address,
    "mac_address": gen_mac_address,
    "driver_license": gen_driver_license,
    "pcn": gen_pcn,
}

# Minimum prefix-mix for cvv: it almost always carries a label in
# practice; emitting it without a prefix word produces an unlabelled
# 3-4-digit number that can be confused with any other short
# numeric. Default 0% no-prefix for cvv, 0% for cvv except inside
# a card-context record (handled by the carrier-template tier 1.5).
CVV_FORCE_PREFIX = True

# Default prefix-mix shares.
DEFAULT_PREFIX_MIX = {
    "no_prefix": 0.25,
    "greek": 0.35,
    "greeklish": 0.20,
    "english": 0.20,
}

# Carrier templates per class, indexed by prefix-mode. Each template
# is a Python format string with `{prefix}` (filled with the prefix
# token + a separator) and `{value}` slots. The `{prefix}` field is
# left empty when prefix_mode == "no_prefix".
CARRIER_TEMPLATES: dict[str, list[str]] = {
    "passport": [
        "Στοιχεία ταξιδιώτη: {prefix}{value}, ταξίδι προς Παρίσι.",
        "Παρακαλώ επιβεβαιώστε τα στοιχεία σας: {prefix}{value}.",
        "{prefix}{value} — λήγει σε 3 χρόνια.",
        "Holder: John Doe, {prefix}{value}, issued in Athens.",
        "Αρ. προτεραιότητας 4421. {prefix}{value} ισχύει έως 2030.",
    ],
    "license_plate": [
        "Αναζητήστε το όχημα με {prefix}{value} στο πάρκινγκ.",
        "Ανέφερε ότι το {prefix}{value} σταμάτησε στο φανάρι.",
        "{prefix}{value} — μάρκα Toyota Yaris, χρώμα μαύρο.",
        "Vehicle plate {prefix}{value} flagged for inspection.",
    ],
    "vehicle_vin": [
        "Παρακαλώ καταχωρίστε το {prefix}{value} στο μητρώο.",
        "Ο αριθμός πλαισίου {prefix}{value} ταιριάζει με τη δήλωσή σας.",
        "Service ticket: {prefix}{value} (model 2018).",
        "Δήλωση παράδοσης: όχημα Νο 4421, {prefix}{value}.",
    ],
    "gemi": [
        "Στοιχεία επιχείρησης: {prefix}{value}.",
        "Η εταιρεία είναι εγγεγραμμένη με {prefix}{value} στη Γενική Γραμματεία.",
        "Παρακαλώ επιβεβαιώστε το {prefix}{value} πριν την υπογραφή.",
        "Business registration {prefix}{value} verified.",
    ],
    "ama": [
        "Στοιχεία ασφαλισμένου: {prefix}{value}.",
        "Παρακαλώ συμπληρώστε τη φόρμα με {prefix}{value}.",
        "{prefix}{value} — δικαιούται επιδόματος.",
        "Insured ID {prefix}{value} on file.",
    ],
    "card_pan": [
        "Στοιχεία κάρτας: {prefix}{value}, ληγμένη.",
        "Παρακαλώ ολοκληρώστε την αγορά με {prefix}{value}.",
        "{prefix}{value} χρεώθηκε με 250,00€.",
        "Charged on card {prefix}{value}.",
    ],
    "cvv": [
        "Στοιχεία κάρτας: 4111 1111 1111 1111, λήξη 12/2027, {prefix}{value}.",
        "Παρακαλώ συμπληρώστε {prefix}{value} για να ολοκληρωθεί η συναλλαγή.",
        "Card 5555 4444 3333 2222 expiry 03/2028 {prefix}{value}.",
    ],
    "imei": [
        "Συσκευή: Samsung Galaxy. {prefix}{value}.",
        "Ο αριθμός IMEI της κλεμμένης συσκευής είναι {prefix}{value}.",
        "Phone {prefix}{value} reported lost.",
    ],
    "ip_address": [
        "Σύνδεση από {prefix}{value}.",
        "Ο διακομιστής {prefix}{value} έδωσε σφάλμα 503.",
        "Failed login from {prefix}{value} at 03:17 UTC.",
        "{prefix}{value} — προστέθηκε στη μαύρη λίστα.",
    ],
    "mac_address": [
        "Συσκευή με {prefix}{value} συνδέθηκε στο δίκτυο.",
        "Παρακαλώ καταχωρίστε το {prefix}{value} στον switch.",
        "DHCP lease for {prefix}{value} expired.",
    ],
    "driver_license": [
        "Στοιχεία οδηγού: {prefix}{value}.",
        "Παρακαλώ επιδείξτε το {prefix}{value} στον αστυνομικό.",
        "{prefix}{value} ανανεώθηκε τον περασμένο μήνα.",
        "Driver license {prefix}{value} valid through 2031.",
    ],
    "pcn": [
        "Στοιχεία πολίτη: {prefix}{value}.",
        "Συμπληρώστε το {prefix}{value} στη φόρμα.",
        "{prefix}{value} — εκδόθηκε το 2025.",
        "Citizen ID {prefix}{value} verified.",
    ],
}

# A small set of sentence frames for the no-prefix mode. The value
# is dropped into the {value} slot and stands without any label.
NO_PREFIX_FRAMES: dict[str, list[str]] = {
    "passport": [
        "Στείλε μου το {value} για την επαλήθευση.",
        "Ο ταξιδιώτης δήλωσε {value} κατά τον έλεγχο.",
    ],
    "license_plate": [
        "Είδα το {value} να φεύγει με ταχύτητα.",
        "Παρακολούθησα το {value} μέχρι την εθνική.",
    ],
    "vehicle_vin": [
        "Το όχημα {value} είναι του 2018.",
        "Έλεγχος ολοκληρώθηκε στο {value}.",
    ],
    "gemi": [
        "Η εταιρεία {value} εκδίδει τιμολόγια στην Πάτρα.",
    ],
    "ama": [
        "Ο αριθμός {value} αντιστοιχεί στον ασφαλισμένο.",
    ],
    "card_pan": [
        "Καταχωρίστε {value} στο σύστημα.",
    ],
    "cvv": [],  # cvv always carries a label
    "imei": [
        "Η συσκευή με {value} είναι κλεμμένη.",
    ],
    "ip_address": [
        "Σύνδεση από {value} στις 14:00.",
        "Το request από {value} επέστρεψε 200.",
    ],
    "mac_address": [
        "Η διεύθυνση {value} εμφανίστηκε ξανά στο log.",
    ],
    "driver_license": [
        "Ο οδηγός παρουσίασε {value} στον τροχονόμο.",
    ],
    "pcn": [
        "Ο αριθμός {value} εκδόθηκε από το ΚΕΠ Αθηνών.",
    ],
}


@dataclass
class GeneratedRecord:
    text: str
    span_start: int
    span_end: int
    category: str
    prefix_mode: str
    difficulty: str = "easy"

    def to_jsonl(self, source: str = "tier1_synthetic") -> str:
        payload = {
            "text": self.text,
            "label": [
                {
                    "category": self.category,
                    "start": self.span_start,
                    "end": self.span_end,
                }
            ],
            "info": {
                "difficulty": self.difficulty,
                "domain": f"tier1:{self.category}",
                "source": source,
                "strategy": f"deterministic_template/{self.prefix_mode}",
            },
        }
        return json.dumps(payload, ensure_ascii=False)


def pick_prefix(
    rng: random.Random, klass: str, mix: dict[str, float]
) -> tuple[str, str]:
    """Return (prefix_mode, prefix_string).

    prefix_string is the formatted prefix slot, including a trailing
    separator (": ", " ", or "."). It is placed before the value in
    the carrier template. In no-prefix mode it is an empty string.
    """
    if klass == "cvv" and CVV_FORCE_PREFIX and rng.random() > 0.0:
        # cvv never appears without a label in practice; force a
        # prefix even if mix says otherwise.
        modes = ["greek", "greeklish", "english"]
        weights = [
            mix["greek"],
            mix["greeklish"],
            mix["english"],
        ]
        mode = rng.choices(modes, weights=weights)[0]
    else:
        modes = ["no_prefix", "greek", "greeklish", "english"]
        weights = [
            mix["no_prefix"],
            mix["greek"],
            mix["greeklish"],
            mix["english"],
        ]
        mode = rng.choices(modes, weights=weights)[0]
    if mode == "no_prefix":
        return mode, ""
    token = rng.choice(PREFIXES[klass][mode])
    sep = rng.choice([": ", " ", ".: ", " - "])
    return mode, f"{token}{sep}"


def build_record(
    rng: random.Random,
    klass: str,
    mix: dict[str, float],
) -> GeneratedRecord:
    value = VALUE_GENERATORS[klass](rng)
    mode, prefix_str = pick_prefix(rng, klass, mix)
    if mode == "no_prefix":
        templates = NO_PREFIX_FRAMES[klass] or CARRIER_TEMPLATES[klass]
    else:
        templates = CARRIER_TEMPLATES[klass]
    template = rng.choice(templates)
    text = template.format(prefix=prefix_str, value=value)
    span_start = text.index(value)
    span_end = span_start + len(value)
    # Sanity: the span covers the value only.
    assert text[span_start:span_end] == value, (
        f"span mismatch: text[{span_start}:{span_end}]"
        f"={text[span_start:span_end]!r} value={value!r}"
    )
    # Sanity: no recognised prefix token starts the span.
    assert not any(
        text[span_start:].startswith(p)
        for ps in PREFIXES[klass].values()
        for p in ps
    ), f"prefix-leak in span for {klass}: {text[span_start:span_end]!r}"
    return GeneratedRecord(
        text=text,
        span_start=span_start,
        span_end=span_end,
        category=klass,
        prefix_mode=mode,
    )


def parse_prefix_mix(s: str | None) -> dict[str, float]:
    if not s:
        return DEFAULT_PREFIX_MIX
    parts = {}
    for piece in s.split(","):
        if "=" not in piece:
            raise ValueError(f"bad --prefix-mix piece: {piece!r}")
        key, val = piece.split("=", 1)
        parts[key.strip()] = float(val.strip())
    expected = {"no_prefix", "greek", "greeklish", "english"}
    if set(parts) != expected:
        raise ValueError(
            f"--prefix-mix must specify {expected}, got {set(parts)}"
        )
    total = sum(parts.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"--prefix-mix shares must sum to 1.0, got {total}")
    return parts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--classes",
        nargs="+",
        required=True,
        choices=list(VALUE_GENERATORS.keys()),
        help="One or more class names to generate.",
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of records to generate per class.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2024,
        help="RNG seed. Same seed + same args = byte-identical output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the JSONL output. Parent dirs are created.",
    )
    parser.add_argument(
        "--prefix-mix",
        default=None,
        help=(
            "Override the prefix-mode mix as comma-separated pairs, e.g. "
            "no_prefix=0.30,greek=0.30,greeklish=0.20,english=0.20. "
            "Shares must sum to 1.0."
        ),
    )
    parser.add_argument(
        "--source-tag",
        default="tier1_synthetic",
        help="Value to write into info.source for each record.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mix = parse_prefix_mix(args.prefix_mix)
    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    counts_by_mode: dict[str, dict[str, int]] = {}
    with args.output.open("w", encoding="utf-8") as fh:
        for klass in args.classes:
            counts_by_mode[klass] = {
                "no_prefix": 0,
                "greek": 0,
                "greeklish": 0,
                "english": 0,
            }
            for _ in range(args.count):
                record = build_record(rng, klass, mix)
                fh.write(record.to_jsonl(source=args.source_tag) + "\n")
                counts_by_mode[klass][record.prefix_mode] += 1
                written += 1
    print(f"[generate_tier1_records] wrote {written} records to {args.output}")
    for klass, modes in counts_by_mode.items():
        total = sum(modes.values())
        share = {k: round(100.0 * v / total, 1) for k, v in modes.items()}
        print(f"  {klass:<16s} {modes} pct={share}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
