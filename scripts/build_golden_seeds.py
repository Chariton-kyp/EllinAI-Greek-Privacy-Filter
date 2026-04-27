"""Hand-authored Greek PII seed examples for Meltemi few-shot generation.

Every example is original prose written for this project and is released
under the same license as the rest of the repository. Run once to emit
`data/seed/golden_examples.jsonl`. Re-run if you edit the inline data.

Usage:

    python scripts/build_golden_seeds.py
"""
from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build(text: str, pairs: list[tuple[str, str]], difficulty: str,
           domain: str) -> dict:
    """Locate each (category, value) in `text` sequentially and emit spans."""
    spans = []
    cursor = 0
    for category, value in pairs:
        idx = text.find(value, cursor)
        if idx < 0:
            raise ValueError(
                f"Value {value!r} not found in {text!r} from cursor {cursor}"
            )
        spans.append(
            {"category": category, "start": idx, "end": idx + len(value)}
        )
        cursor = idx + len(value)
    return {
        "text": text,
        "label": spans,
        "info": {
            "difficulty": difficulty,
            "domain": domain,
            "source": "golden_seeds",
        },
    }


EASY: list[dict] = [
    _build(
        "Ο ασθενής έχει ΑΜΚΑ 15027299045 και ζητά αντίγραφο ιστορικού.",
        [("amka", "15027299045")],
        "easy", "medical",
    ),
    _build(
        "Ο ΑΦΜ της εταιρείας είναι 123456789 για την τιμολόγηση.",
        [("afm", "123456789")],
        "easy", "tax_docs",
    ),
    _build(
        "Κατά τον έλεγχο παρουσίασε την ταυτότητα ΑΒ 123456.",
        [("adt", "ΑΒ 123456")],
        "easy", "public_service",
    ),
    _build(
        "Κατάθεσε το ποσό στον λογαριασμό GR1601101250000000012300695.",
        [("iban_gr", "GR1601101250000000012300695")],
        "easy", "banking",
    ),
    _build(
        "Ο Γιώργος Παπαδόπουλος ήρθε για συνέντευξη σήμερα στις 10:00.",
        [("private_person", "Γιώργος Παπαδόπουλος")],
        "easy", "job_application",
    ),
    _build(
        "Καλέστε στο 6944123456 για πληροφορίες σχετικά με την κράτηση.",
        [("private_phone", "6944123456")],
        "easy", "hotel_booking",
    ),
    _build(
        "Στείλε email στο info@example.gr αν θέλεις λεπτομέρειες τιμολόγησης.",
        [("private_email", "info@example.gr")],
        "easy", "business_email",
    ),
    _build(
        "Δες το προφίλ στο linkedin.com/in/petropoulos για περισσότερα.",
        [("private_url", "linkedin.com/in/petropoulos")],
        "easy", "forums",
    ),
    _build(
        "Η διεύθυνση αποστολής είναι Πατησίων 76, Αθήνα 10434.",
        [("private_address", "Πατησίων 76, Αθήνα 10434")],
        "easy", "food_delivery",
    ),
    _build(
        "Η ημερομηνία γέννησης είναι 14/03/1985 σύμφωνα με την αίτηση.",
        [("private_date", "14/03/1985")],
        "easy", "hr",
    ),
    _build(
        "Ο αριθμός λογαριασμού πελάτη είναι 012345678901 στο σύστημά μας.",
        [("account_number", "012345678901")],
        "easy", "crm",
    ),
    _build(
        "Το development API key είναι sk-ABC123XYZ456DEF789GHI000, μην το κοινοποιείς.",
        [("secret", "sk-ABC123XYZ456DEF789GHI000")],
        "easy", "code_comments",
    ),
]


MEDIUM: list[dict] = [
    _build(
        "Η πελάτισσα Μαρία Ιωάννου (ΑΦΜ 098765432) κατέθεσε στον IBAN "
        "GR9001401140114002320001234.",
        [
            ("private_person", "Μαρία Ιωάννου"),
            ("afm", "098765432"),
            ("iban_gr", "GR9001401140114002320001234"),
        ],
        "medium", "banking",
    ),
    _build(
        "Στέλνω βιογραφικό στο maria.ioannou@gmail.com. "
        "Τηλέφωνο επικοινωνίας: 2108123456.",
        [
            ("private_email", "maria.ioannou@gmail.com"),
            ("private_phone", "2108123456"),
        ],
        "medium", "job_application",
    ),
    _build(
        "Η ΑΜΚΑ 22089145678 αντιστοιχεί στον Νίκο Δημητρίου, οδός Ερμού 45, "
        "Θεσσαλονίκη 54625.",
        [
            ("amka", "22089145678"),
            ("private_person", "Νίκο Δημητρίου"),
            ("private_address", "Ερμού 45, Θεσσαλονίκη 54625"),
        ],
        "medium", "medical",
    ),
    _build(
        "Το ραντεβού του Ιωάννη Παπαδόπουλου είναι στις 12/05/2024 "
        "στη διεύθυνση Σόλωνος 25, Αθήνα 10672.",
        [
            ("private_person", "Ιωάννη Παπαδόπουλου"),
            ("private_date", "12/05/2024"),
            ("private_address", "Σόλωνος 25, Αθήνα 10672"),
        ],
        "medium", "legal",
    ),
    _build(
        "Κατάθεση από τον Δημήτρη Αντωνίου (ΑΔΤ ΑΒ-987654) στον αριθμό "
        "λογαριασμού 987654321000.",
        [
            ("private_person", "Δημήτρη Αντωνίου"),
            ("adt", "ΑΒ-987654"),
            ("account_number", "987654321000"),
        ],
        "medium", "banking",
    ),
    _build(
        "Η συνδρομή στο ενημερωτικό δελτίο απαιτεί email (π.χ. "
        "kostas.vlachos@outlook.com) και κωδικό OTP που στάλθηκε στο 6987123456.",
        [
            ("private_email", "kostas.vlachos@outlook.com"),
            ("private_phone", "6987123456"),
        ],
        "medium", "marketing",
    ),
    _build(
        "Σε περίπτωση απώλειας επικοινωνήστε στο support@trapeza.gr ή "
        "καλέστε 2109876543. ΑΦΜ δικαιούχου: 567890123.",
        [
            ("private_email", "support@trapeza.gr"),
            ("private_phone", "2109876543"),
            ("afm", "567890123"),
        ],
        "medium", "banking",
    ),
    _build(
        "Παρακαλούμε επιβεβαιώστε τον IBAN GR8502600030110000001234567 και "
        "στείλτε αποδεικτικό στο finance@company.gr μέχρι 30/11/2024.",
        [
            ("iban_gr", "GR8502600030110000001234567"),
            ("private_email", "finance@company.gr"),
            ("private_date", "30/11/2024"),
        ],
        "medium", "business_email",
    ),
    _build(
        "Η ασθενής Ελένη Νικολάου (ΑΜΚΑ 01018574321) έχει ραντεβού στις "
        "03 Μαρ 2025 στο τηλέφωνο 2310456789.",
        [
            ("private_person", "Ελένη Νικολάου"),
            ("amka", "01018574321"),
            ("private_date", "03 Μαρ 2025"),
            ("private_phone", "2310456789"),
        ],
        "medium", "medical",
    ),
    _build(
        "Η αίτηση για κάρτα ανεργίας κατατέθηκε από τον Θανάση Γεωργίου "
        "(ΑΦΜ 234567891, ΑΜΚΑ 25067892345) στις 10/01/2025.",
        [
            ("private_person", "Θανάση Γεωργίου"),
            ("afm", "234567891"),
            ("amka", "25067892345"),
            ("private_date", "10/01/2025"),
        ],
        "medium", "public_service",
    ),
    _build(
        "Ο πωλητής κοινοποίησε λινκ προϊόντος: instagram.com/shop_greek23 "
        "και τηλέφωνο παραγγελιών +30 6912345678.",
        [
            ("private_url", "instagram.com/shop_greek23"),
            ("private_phone", "+30 6912345678"),
        ],
        "medium", "ecommerce",
    ),
    _build(
        "Ο κωδικός ασφαλείας στο .env αρχείο είναι "
        "sk-prod-9A8B7C6D5E4F3G2H1I0J και δεν πρέπει να ανέβει στο git.",
        [("secret", "sk-prod-9A8B7C6D5E4F3G2H1I0J")],
        "medium", "code_comments",
    ),
    _build(
        "Η εταιρεία ACME με ΑΦΜ 345678912 πλήρωσε το τιμολόγιο στον "
        "IBAN GR1502600010110000009876543 στις 28/02/2025.",
        [
            ("afm", "345678912"),
            ("iban_gr", "GR1502600010110000009876543"),
            ("private_date", "28/02/2025"),
        ],
        "medium", "tax_docs",
    ),
    _build(
        "Ζητήθηκε επανακατάθεση του Στέλιου Βλάχου (ΑΔΤ ΑΒΓ 456123) στον "
        "λογαριασμό 555111222333.",
        [
            ("private_person", "Στέλιου Βλάχου"),
            ("adt", "ΑΒΓ 456123"),
            ("account_number", "555111222333"),
        ],
        "medium", "banking",
    ),
    _build(
        "Ο χρήστης github.com/katerina42 ζήτησε να προστεθεί στην ομάδα "
        "μέσω email katerina.dimou@yahoo.gr.",
        [
            ("private_url", "github.com/katerina42"),
            ("private_email", "katerina.dimou@yahoo.gr"),
        ],
        "medium", "forums",
    ),
]


HARD: list[dict] = [
    _build(
        "Η Ελένη δήλωσε ΑΜΚΑ 01019580001 στη φόρμα με έγκυρη ΑΔΤ "
        "ΑΖ-123987, διεύθυνση Βασιλίσσης Σοφίας 120, Αθήνα 11528, και "
        "ημερομηνία υποβολής 18/12/2023.",
        [
            ("private_person", "Ελένη"),
            ("amka", "01019580001"),
            ("adt", "ΑΖ-123987"),
            ("private_address", "Βασιλίσσης Σοφίας 120, Αθήνα 11528"),
            ("private_date", "18/12/2023"),
        ],
        "hard", "legal",
    ),
    _build(
        "# TODO: κώδικας = sk-dev-ABCDEF123456; contact dev@mail.gr ή "
        "6944112233 αν χρειάζεται rotation του secret.",
        [
            ("secret", "sk-dev-ABCDEF123456"),
            ("private_email", "dev@mail.gr"),
            ("private_phone", "6944112233"),
        ],
        "hard", "code_comments",
    ),
    _build(
        "Ο Παναγιώτης Οικονόμου κατέθεσε €3.500 στον IBAN "
        "GR33 0110 1250 0000 0123 4567 890 με αναφορά #PAY-2024-00789.",
        [
            ("private_person", "Παναγιώτης Οικονόμου"),
            ("iban_gr", "GR33 0110 1250 0000 0123 4567 890"),
            ("account_number", "PAY-2024-00789"),
        ],
        "hard", "banking",
    ),
    _build(
        "Υπεύθυνος επεξεργασίας: Αντώνης Μιχαηλίδης (ΑΦΜ 456789012), "
        "διεύθυνση οργανισμού Κηφισίας 88, Μαρούσι 15125, τηλ. "
        "210.111.2233, email a.mihailidis@company.com.",
        [
            ("private_person", "Αντώνης Μιχαηλίδης"),
            ("afm", "456789012"),
            ("private_address", "Κηφισίας 88, Μαρούσι 15125"),
            ("private_phone", "210.111.2233"),
            ("private_email", "a.mihailidis@company.com"),
        ],
        "hard", "gdpr_notice",
    ),
    _build(
        "Στην πλατφόρμα διαχείρισης είδαν τη σύνδεση: χρήστης "
        "twitter.com/sofia_g23, ημερομηνία 07-02-2025 στις 14:37, IP "
        "192.168.1.45, αριθμός αίτησης 000234567.",
        [
            ("private_url", "twitter.com/sofia_g23"),
            ("private_date", "07-02-2025"),
            ("account_number", "000234567"),
        ],
        "hard", "security_log",
    ),
    _build(
        "Ασθενής: Αγγελική Θεοδώρου, γεν. 1965. ΑΜΚΑ 15075600123, "
        "ΑΦΜ 112233445, τηλέφωνο 6944998877, διεύθυνση Αριστοτέλους 12, "
        "Θεσσαλονίκη 54623.",
        [
            ("private_person", "Αγγελική Θεοδώρου"),
            ("amka", "15075600123"),
            ("afm", "112233445"),
            ("private_phone", "6944998877"),
            ("private_address", "Αριστοτέλους 12, Θεσσαλονίκη 54623"),
        ],
        "hard", "medical",
    ),
    _build(
        "Μήνυμα στο ticket #88123: ο πελάτης ζήτησε επιστροφή χρημάτων "
        "στον IBAN GR0801101250000000012300333 μέσω του email "
        "mpalais.xaris@forthnet.gr, ΑΔΤ ΑΚ 554433.",
        [
            ("account_number", "88123"),
            ("iban_gr", "GR0801101250000000012300333"),
            ("private_email", "mpalais.xaris@forthnet.gr"),
            ("adt", "ΑΚ 554433"),
        ],
        "hard", "customer_support",
    ),
    _build(
        "Παραλήπτης δέματος: Χριστίνα Σταματίου, Μιχαλακοπούλου 200, "
        "Αθήνα 11527. Τηλ. κινητό 6999001122, σταθερό 2106655443.",
        [
            ("private_person", "Χριστίνα Σταματίου"),
            ("private_address", "Μιχαλακοπούλου 200, Αθήνα 11527"),
            ("private_phone", "6999001122"),
            ("private_phone", "2106655443"),
        ],
        "hard", "courier",
    ),
]


HARD_NEGATIVE: list[dict] = [
    _build(
        "Η εταιρεία OpenAI ανακοίνωσε νέα μοντέλα τεχνητής νοημοσύνης στο "
        "Σαν Φρανσίσκο.",
        [],
        "hard_negative", "press",
    ),
    _build(
        "Ο Δήμος Αθηναίων δημοσίευσε την ετήσια έκθεση πεπραγμένων για το 2024.",
        [],
        "hard_negative", "press",
    ),
    _build(
        "Ο όρος IBAN αναφέρεται στον διεθνή αριθμό τραπεζικού λογαριασμού "
        "και ορίζεται από το ISO 13616.",
        [],
        "hard_negative", "definition",
    ),
    _build(
        "Το Σύνταγμα της Ελλάδας ψηφίστηκε το 1975 και έχει αναθεωρηθεί "
        "αρκετές φορές έκτοτε.",
        [],
        "hard_negative", "press",
    ),
    _build(
        "Το ΑΦΜ είναι ένα εννιαψήφιο νούμερο που δίνεται στους φορολογούμενους "
        "από την ΑΑΔΕ.",
        [],
        "hard_negative", "definition",
    ),
    _build(
        "Ο κωδικός σφάλματος HTTP 404 σημαίνει ότι η σελίδα δεν βρέθηκε.",
        [],
        "hard_negative", "code_comments",
    ),
    _build(
        "Η Ελληνική Στατιστική Αρχή δημοσίευσε νέα στοιχεία για το ΑΕΠ "
        "του τρίτου τριμήνου.",
        [],
        "hard_negative", "press",
    ),
]


def main() -> None:
    out_path = PROJECT_ROOT / "data" / "seed" / "golden_examples.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_examples = EASY + MEDIUM + HARD + HARD_NEGATIVE
    with out_path.open("w", encoding="utf-8") as fp:
        for ex in all_examples:
            fp.write(json.dumps(ex, ensure_ascii=False) + "\n")
    by_tier: dict[str, int] = {}
    for ex in all_examples:
        by_tier[ex["info"]["difficulty"]] = (
            by_tier.get(ex["info"]["difficulty"], 0) + 1
        )
    print(f"Wrote {len(all_examples)} golden seed examples to {out_path}")
    print(f"By tier: {by_tier}")


if __name__ == "__main__":
    main()
