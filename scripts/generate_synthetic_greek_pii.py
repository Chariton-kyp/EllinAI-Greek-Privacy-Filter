from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Greek PII dataset in OPF label format."
    )
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--count", type=int, default=200, help="Number of examples.")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed.")
    return parser.parse_args()


def _resolve(path_value: str, project_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def _labelize(text: str, spans: list[tuple[str, str]]) -> dict:
    labels: list[dict[str, int | str]] = []
    used_from: dict[str, int] = {}
    for span_text, category in spans:
        start_at = used_from.get(span_text, 0)
        start = text.find(span_text, start_at)
        if start < 0:
            start = text.find(span_text)
        if start < 0:
            raise ValueError(f"Could not find span {span_text!r} in text {text!r}")
        end = start + len(span_text)
        labels.append({"category": category, "start": start, "end": end})
        used_from[span_text] = end
    return {"text": text, "label": labels}


def generate_dataset(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)

    first_names = [
        "Γιώργος",
        "Μαρία",
        "Νίκος",
        "Ελένη",
        "Δημήτρης",
        "Κατερίνα",
        "Αντώνης",
        "Σοφία",
        "Παναγιώτης",
        "Χριστίνα",
    ]
    surnames = [
        "Παπαδόπουλος",
        "Αντωνίου",
        "Κωνσταντίνου",
        "Νικολάου",
        "Γεωργίου",
        "Δημητρίου",
        "Καραγιάννη",
        "Σταματίου",
    ]
    streets = ["Ερμού", "Σταδίου", "Αθηνάς", "Τσιμισκή", "Πανεπιστημίου", "Πατησίων"]
    cities = ["Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Λάρισα", "Βόλος", "Ηράκλειο"]
    domains = ["gmail.com", "yahoo.gr", "otenet.gr", "outlook.com"]
    public_figures = [
        "Κυριάκος Μητσοτάκης",
        "Αλέξης Τσίπρας",
        "Μαρία Κάλλας",
        "Ελευθέριος Βενιζέλος",
        "Μίκης Θεοδωράκης",
    ]
    organizations = ["Εθνική Τράπεζα", "ΔΕΗ", "COSMOTE", "Vodafone", "ΕΥΔΑΠ"]

    negatives_target = max(1, int(count * 0.2))
    positives_target = count - negatives_target
    rows: list[dict] = []

    for i in range(positives_target):
        fn = rng.choice(first_names)
        sn = rng.choice(surnames)
        full_name = f"{fn} {sn}"
        phone = f"69{rng.randint(10,99)}{rng.randint(100000,999999)}"
        email = f"{fn.lower()}.{sn.lower()}{rng.randint(1,99)}@{rng.choice(domains)}"
        address = f"{rng.choice(streets)} {rng.randint(1,120)}, {rng.choice(cities)} {rng.randint(10000,99999)}"
        date = f"{rng.randint(1,28):02d}/{rng.randint(1,12):02d}/{rng.randint(1970,2002)}"
        afm = f"{rng.randint(0,999999999):09d}"
        amka = f"{rng.randint(1,28):02d}{rng.randint(1,12):02d}{rng.randint(70,99):02d}{rng.randint(10000,99999):05d}"
        letters = "".join(rng.choice("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ") for _ in range(2))
        adt = f"{letters}{rng.randint(100000,999999)}"
        iban = "GR16 " + " ".join(
            [
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,9999):04d}",
                f"{rng.randint(0,999):03d}",
            ]
        )
        account_number = f"{rng.randint(1000,9999)} {rng.randint(1000,9999)} {rng.randint(1000,9999)} {rng.randint(1000,9999)}"
        secret = f"sk-proj-{rng.choice('abcdefghijklmnopqrstuvwxyz')}{rng.randint(10000,99999)}xyz"
        url = f"instagram.com/{fn.lower()}{rng.randint(10,99)}"

        template_id = i % 10
        if template_id == 0:
            text = f"Ο {full_name} έχει τηλέφωνο {phone} και email {email}."
            spans = [(full_name, "private_person"), (phone, "private_phone"), (email, "private_email")]
        elif template_id == 1:
            text = f"Η διεύθυνση του {full_name} είναι {address}."
            spans = [(full_name, "private_person"), (address, "private_address")]
        elif template_id == 2:
            text = f"Στοιχεία πελάτη: ΑΦΜ {afm}, ΑΜΚΑ {amka}, ονοματεπώνυμο {full_name}."
            spans = [(afm, "afm"), (amka, "amka"), (full_name, "private_person")]
        elif template_id == 3:
            text = f"Δήλωσε ΑΔΤ {adt} και ημερομηνία γέννησης {date}."
            spans = [(adt, "adt"), (date, "private_date")]
        elif template_id == 4:
            text = f"IBAN για πληρωμή: {iban}. Λογαριασμός κάρτας {account_number}."
            spans = [(iban, "iban_gr"), (account_number, "account_number")]
        elif template_id == 5:
            text = f"Το μυστικό token είναι {secret}. Στείλτο στο {email}."
            spans = [(secret, "secret"), (email, "private_email")]
        elif template_id == 6:
            text = f"Το προφίλ του {full_name} είναι {url}."
            spans = [(full_name, "private_person"), (url, "private_url")]
        elif template_id == 7:
            text = f"Ο {full_name} γεννήθηκε στις {date} και μένει στην {address}."
            spans = [(full_name, "private_person"), (date, "private_date"), (address, "private_address")]
        elif template_id == 8:
            text = f"Κάλεσε στο {phone} για τον πελάτη με ΑΦΜ {afm}."
            spans = [(phone, "private_phone"), (afm, "afm")]
        else:
            text = f"Επικοινωνία: {full_name}, email {email}, ΑΔΤ {adt}, IBAN {iban}."
            spans = [(full_name, "private_person"), (email, "private_email"), (adt, "adt"), (iban, "iban_gr")]

        rows.append(_labelize(text, spans))

    for i in range(negatives_target):
        if i % 4 == 0:
            text = f"Η είδηση αφορά τον {rng.choice(public_figures)} και τη χθεσινή ομιλία."
        elif i % 4 == 1:
            text = "ΟΝΟΜΑΤΕΠΩΝΥΜΟ: ____ , EMAIL: {email}, ΔΙΕΥΘΥΝΣΗ: [insert address]"
        elif i % 4 == 2:
            text = f"Η ανακοίνωση της {rng.choice(organizations)} αφορά νέο τιμολόγιο."
        else:
            text = "Ένας πελάτης ζήτησε πληροφορίες χωρίς να δώσει προσωπικά στοιχεία."
        rows.append({"text": text, "label": []})

    rng.shuffle(rows)
    return rows[:count]


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    output_path = _resolve(args.output, project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = generate_dataset(args.count, args.seed)
    with output_path.open("w", encoding="utf-8") as outfile:
        for row in rows:
            outfile.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} synthetic examples to {output_path}")


if __name__ == "__main__":
    main()
