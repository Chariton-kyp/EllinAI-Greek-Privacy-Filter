from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path


LABELS = [
    "private_person",
    "private_address",
    "private_phone",
    "private_email",
    "private_url",
    "private_date",
    "account_number",
    "secret",
    "afm",
    "amka",
    "adt",
    "iban_gr",
]


DOMAINS = [
    "customer_service",
    "banking",
    "medical",
    "classified_ads",
    "forums",
    "business_email",
    "sms_dm",
    "cv",
    "tax_docs",
    "rental",
    "school",
    "code_comments",
    "food_delivery",
    "job_application",
    "property_listing",
]


PUBLIC_FIGURES = [
    "Κυριάκος Μητσοτάκης",
    "Αλέξης Τσίπρας",
    "Γιώργος Παπανδρέου",
    "Μαρία Κάλλας",
    "Ελευθέριος Βενιζέλος",
    "Μίκης Θεοδωράκης",
]

FICTIONAL = ["Οδυσσέας", "Αλέξης Ζορμπάς", "Καραγκιόζης", "Διγενής Ακρίτας"]
ORGS = ["Εθνική Τράπεζα", "ΔΕΗ", "COSMOTE", "ΕΥΔΑΠ", "Vodafone", "Nova"]


@dataclass(frozen=True)
class DifficultyConfig:
    name: str
    min_spans: int
    max_spans: int
    min_chars: int
    max_chars: int
    noise: bool


DIFFICULTIES = [
    DifficultyConfig("easy", 1, 2, 60, 140, False),
    DifficultyConfig("medium", 2, 3, 110, 260, True),
    DifficultyConfig("hard", 3, 5, 200, 500, True),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Greek OPF examples with increasing difficulty."
    )
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--count", type=int, default=720, help="Example count")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed")
    parser.add_argument(
        "--profile",
        choices=("mixed", "hard_eval"),
        default="mixed",
        help="Difficulty profile for generation.",
    )
    parser.add_argument(
        "--negatives-ratio",
        type=float,
        default=0.2,
        help="Ratio of hard negatives (0.0 - 0.5).",
    )
    return parser.parse_args()


def _resolve(path_value: str, project_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def _find_labels(text: str, spans: list[tuple[str, str]]) -> list[dict[str, int | str]]:
    labels: list[dict[str, int | str]] = []
    used_positions: dict[str, int] = {}
    for span_text, category in spans:
        start_pos = used_positions.get(span_text, 0)
        idx = text.find(span_text, start_pos)
        if idx < 0:
            idx = text.find(span_text)
        if idx < 0:
            raise ValueError(f"Span {span_text!r} not found in text.")
        end = idx + len(span_text)
        labels.append({"category": category, "start": idx, "end": end})
        used_positions[span_text] = end
    return labels


def _choice_name(rng: random.Random) -> tuple[str, str]:
    first = rng.choice(
        [
            "Γιώργος",
            "Μαρία",
            "Νίκος",
            "Ελένη",
            "Δημήτρης",
            "Κατερίνα",
            "Παναγιώτης",
            "Σοφία",
            "Χριστίνα",
            "Αντώνης",
        ]
    )
    last = rng.choice(
        [
            "Παπαδόπουλος",
            "Αντωνίου",
            "Κωνσταντίνου",
            "Νικολάου",
            "Γεωργίου",
            "Καραγιάννη",
            "Δημητρίου",
            "Σταματίου",
        ]
    )
    return first, last


def _value_for(label: str, rng: random.Random) -> str:
    first, last = _choice_name(rng)
    if label == "private_person":
        variants = [
            f"{first} {last}",
            f"του {first} {last}",
            f"τον {first} {last}",
            f"κ. {last}",
            f"Δρ. {last}",
            f"{last} {first}",
        ]
        return rng.choice(variants)
    if label == "private_address":
        street = rng.choice(["Ερμού", "Σταδίου", "Αθηνάς", "Πατησίων", "Τσιμισκή"])
        city = rng.choice(["Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Λάρισα", "Βόλος"])
        return f"{street} {rng.randint(1,120)}, {city} {rng.randint(10000,99999)}"
    if label == "private_phone":
        patterns = [
            f"69{rng.randint(10,99)}{rng.randint(100000,999999)}",
            f"+30 210 {rng.randint(1000000,9999999)}",
            f"210-{rng.randint(1000000,9999999)}",
            f"2310 {rng.randint(100000,999999)}",
        ]
        return rng.choice(patterns)
    if label == "private_email":
        return f"{first.lower()}.{last.lower()}{rng.randint(1,99)}@{rng.choice(['gmail.com','otenet.gr','outlook.com','yahoo.gr'])}"
    if label == "private_url":
        return rng.choice(
            [
                f"instagram.com/{first.lower()}{rng.randint(10,99)}",
                f"linkedin.com/in/{first.lower()}{last.lower()}",
            ]
        )
    if label == "private_date":
        return rng.choice(
            [
                f"{rng.randint(1,28):02d}/{rng.randint(1,12):02d}/{rng.randint(1970,2002)}",
                f"{rng.randint(1,28):02d}-{rng.randint(1,12):02d}-{rng.randint(1970,2002)}",
                str(rng.randint(1970, 2002)),
            ]
        )
    if label == "account_number":
        return f"{rng.randint(1000,9999)} {rng.randint(1000,9999)} {rng.randint(1000,9999)} {rng.randint(1000,9999)}"
    if label == "secret":
        return rng.choice(
            [
                f"sk-proj-{rng.choice('abcdefghijklmnopqrstuvwxyz')}{rng.randint(10000,99999)}xyz",
                f"Gior{rng.randint(1970,2000)}!",
                f"eyJhbGciOi{rng.randint(1000,9999)}",
            ]
        )
    if label == "afm":
        return f"{rng.randint(0,999999999):09d}"
    if label == "amka":
        return f"{rng.randint(1,28):02d}{rng.randint(1,12):02d}{rng.randint(70,99):02d}{rng.randint(10000,99999):05d}"
    if label == "adt":
        letters = "".join(rng.choice("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ") for _ in range(rng.choice([1, 2, 3])))
        sep = rng.choice(["", " ", "-"])
        return f"{letters}{sep}{rng.randint(100000,9999999)}"
    if label == "iban_gr":
        return "GR16 " + " ".join(
            [
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,999):03d}",
            ]
        )
    raise ValueError(f"Unsupported label: {label}")


def _segment_for(label: str, value: str, domain: str, rng: random.Random) -> str:
    patterns = {
        "private_person": [
            f"Ο πελάτης {value} επικοινώνησε ξανά.",
            f"Το αίτημα του {value} καταχωρήθηκε.",
            f"Στο βιογραφικό αναγράφεται το όνομα {value}.",
        ],
        "private_address": [
            f"Διεύθυνση παράδοσης: {value}.",
            f"Στο μισθωτήριο δηλώνεται η κατοικία {value}.",
            f"Το αποδεικτικό αναφέρει τη διεύθυνση {value}.",
        ],
        "private_phone": [
            f"Τηλέφωνο επικοινωνίας: {value}.",
            f"Κάλεσε με αριθμό {value}.",
            f"Στείλε μήνυμα στο {value}.",
        ],
        "private_email": [
            f"Email επικοινωνίας: {value}.",
            f"Η αίτηση εστάλη από {value}.",
            f"Απάντησε στο {value} έως αύριο.",
        ],
        "private_url": [
            f"Το προσωπικό προφίλ είναι {value}.",
            f"Επισύναψε private link {value}.",
        ],
        "private_date": [
            f"ΗΜΝΙΑ ΓΕΝ.: {value}.",
            f"Η γέννηση καταγράφηκε ως {value}.",
        ],
        "account_number": [
            f"Αριθμός λογαριασμού: {value}.",
            f"Κάρτα χρέωσης: {value}.",
        ],
        "secret": [
            f"Κωδικός πρόσβασης: {value}.",
            f"Token ελέγχου: {value}.",
        ],
        "afm": [
            f"ΑΦΜ: {value}.",
            f"Στο Taxisnet εμφανίζεται Α.Φ.Μ. {value}.",
        ],
        "amka": [
            f"ΑΜΚΑ {value} στο ιατρικό αρχείο.",
            f"Καταγράφηκε ΑΜΚΑ {value}.",
        ],
        "adt": [
            f"ΑΔΤ {value} προσκομίστηκε στο γκισέ.",
            f"Στοιχείο ταυτότητας: {value}.",
        ],
        "iban_gr": [
            f"IBAN δικαιούχου: {value}.",
            f"Πίστωση σε λογαριασμό {value}.",
        ],
    }
    segment = rng.choice(patterns[label])
    if domain == "code_comments":
        segment = f"// {segment}"
    if domain == "forums":
        segment = f"[post] {segment}"
    return segment


def _domain_intro(domain: str, rng: random.Random) -> str:
    intro = {
        "customer_service": "Chat εξυπηρέτησης πελάτη με πάροχο ενέργειας.",
        "banking": "Σημείωση τραπεζικής επικοινωνίας.",
        "medical": "Ιατρικό σημείωμα εξωτερικού ιατρείου.",
        "classified_ads": "Κείμενο αγγελίας από πλατφόρμα.",
        "forums": "Ανάρτηση σε ελληνικό forum.",
        "business_email": "Εσωτερικό εταιρικό email.",
        "sms_dm": "Σύντομο προσωπικό μήνυμα.",
        "cv": "Απόσπασμα βιογραφικού σημειώματος.",
        "tax_docs": "Απόσπασμα φορολογικού εγγράφου.",
        "rental": "Απόσπασμα μισθωτηρίου.",
        "school": "Σχολικό/πανεπιστημιακό αρχείο.",
        "code_comments": "Σχόλια κώδικα σε δοκιμαστικό script.",
        "food_delivery": "Οδηγίες παράδοσης φαγητού.",
        "job_application": "Αίτηση εργασίας.",
        "property_listing": "Κείμενο περιγραφής ακινήτου.",
    }
    return intro[domain]


def _negative_text(kind: str, rng: random.Random) -> str:
    if kind == "public":
        return f"Η συζήτηση αφορούσε τον {rng.choice(PUBLIC_FIGURES)} και την πρόσφατη ομιλία."
    if kind == "fictional":
        return f"Στο κείμενο αναφέρονται οι χαρακτήρες {rng.choice(FICTIONAL)} και {rng.choice(FICTIONAL)}."
    if kind == "placeholder":
        return "ΟΝΟΜΑΤΕΠΩΝΥΜΟ: ____ | EMAIL: {email} | ΔΙΕΥΘΥΝΣΗ: [insert address]"
    if kind == "generic":
        return "Ένας πελάτης ρώτησε γενικές πληροφορίες χωρίς να μοιραστεί προσωπικά στοιχεία."
    return f"Ανακοίνωση της {rng.choice(ORGS)} για νέο πακέτο υπηρεσιών."


def generate(count: int, seed: int, profile: str, negatives_ratio: float) -> list[dict]:
    rng = random.Random(seed)
    negatives = int(count * negatives_ratio)
    positives = count - negatives
    rows: list[dict] = []

    if profile == "hard_eval":
        hard = int(positives * 0.6)
        medium = int(positives * 0.3)
        easy = positives - hard - medium
        per_diff = [easy, medium, hard]
    else:
        per_diff = [positives // 3, positives // 3, positives - 2 * (positives // 3)]
    for diff, n_examples in zip(DIFFICULTIES, per_diff):
        for _ in range(n_examples):
            domain = rng.choice(DOMAINS)
            n_spans = rng.randint(diff.min_spans, diff.max_spans)
            categories = rng.sample(LABELS, k=min(n_spans, len(LABELS)))
            values = {cat: _value_for(cat, rng) for cat in categories}
            intro = _domain_intro(domain, rng)
            segments = [_segment_for(cat, values[cat], domain, rng) for cat in categories]
            text = intro + " " + " ".join(segments)
            if diff.noise:
                text += " " + rng.choice(
                    [
                        "Παρακαλώ επιβεβαίωση εντός ημέρας.",
                        "Σημείωση: τα παραπάνω απαιτούν έλεγχο.",
                        "Ευχαριστώ για την άμεση ανταπόκριση.",
                    ]
                )
            spans = [(values[cat], cat) for cat in categories]
            labels = _find_labels(text, spans)
            rows.append(
                {
                    "text": text,
                    "label": labels,
                    "info": {"difficulty": diff.name, "domain": domain},
                }
            )

    negative_kinds = ["public", "fictional", "placeholder", "generic", "org"]
    for idx in range(negatives):
        kind = negative_kinds[idx % len(negative_kinds)]
        domain = rng.choice(DOMAINS)
        text = f"{_domain_intro(domain, rng)} {_negative_text(kind, rng)}"
        rows.append({"text": text, "label": [], "info": {"difficulty": "hard_negative", "domain": domain}})

    rng.shuffle(rows)
    return rows[:count]


def main() -> None:
    args = parse_args()
    if args.count < 1:
        raise ValueError("--count must be > 0")
    if args.negatives_ratio < 0.0 or args.negatives_ratio > 0.5:
        raise ValueError("--negatives-ratio must be between 0.0 and 0.5")
    project_root = Path(__file__).resolve().parents[1]
    output_path = _resolve(args.output, project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = generate(args.count, args.seed, args.profile, args.negatives_ratio)
    with output_path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} curriculum examples to {output_path}")


if __name__ == "__main__":
    main()
