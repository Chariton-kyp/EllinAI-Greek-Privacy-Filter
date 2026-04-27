"""Generate Greek PII training data that is 100% commercially usable.

This generator produces labeled examples where:

  * Carrier text (the sentence surrounding the PII) comes from either:
      - public-domain / CC0 sources (PleIAs/Greek-PD, Mozilla Common Voice
        Greek text), which the user passes in via --carrier-jsonl, or
      - Meltemi-7B-Instruct-v1.5 outputs via Ollama (default Apache-2.0
        Greek-tuned model whose outputs are fully yours), or
      - a built-in template bank (default; no external deps required)
  * PII values (names, AMKA, AFM, ADT, IBAN, phones, emails, URLs,
    addresses, dates) are drawn from rule-based generators in this file,
    so the user is the sole author of those values.

Result: the dataset's copyright chain contains only content you own
outright or have an irrevocable commercial-use right to. You can:
  * use the resulting fine-tuned model commercially yourself, and
  * re-release the model under a non-commercial license to others,
    without contaminating your own commercial rights.

Quick usage (no external deps):

  python scripts/generate_commercial_safe_greek_pii.py \
      --output data/processed/greek_commercial_safe.jsonl \
      --count 2000 --mode templates

With a public-domain / CC0 carrier corpus (safest real-language variant):

  python scripts/generate_commercial_safe_greek_pii.py \
      --output data/processed/greek_commercial_safe.jsonl \
      --count 2000 --mode carrier \
      --carrier-jsonl data/raw/greek_pd_sentences.jsonl

With Meltemi via Ollama (primary production flow):

  ollama pull ilsp/meltemi-instruct-v1.5
  python scripts/generate_commercial_safe_greek_pii.py \
      --output data/processed/greek_commercial_safe.jsonl \
      --count 2000 --mode mix \
      --ollama-model ilsp/meltemi-instruct-v1.5 \
      --few-shot-file data/seed/golden_examples.jsonl

Output schema matches scripts/generate_synthetic_greek_pii.py exactly:
{"text": "...", "label": [{"category": "amka", "start": 12, "end": 23}, ...],
 "info": {"difficulty": "easy|medium|hard|hard_negative",
          "domain": "...", "source": "commercial_safe_generator"}}
"""
from __future__ import annotations

import argparse
import json
import random
import re
import string
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from privacy_filter_ft.transliteration import transliterate_greek  # noqa: E402


# ---------------------------------------------------------------------------
# PII value generators (rule-based; owned by you)
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Γιώργος", "Μαρία", "Νίκος", "Ελένη", "Δημήτρης", "Κατερίνα",
    "Αντώνης", "Σοφία", "Παναγιώτης", "Χριστίνα", "Κώστας", "Αθηνά",
    "Στέλιος", "Ιωάννα", "Βασίλης", "Αγγελική", "Θανάσης", "Δήμητρα",
]
SURNAMES = [
    "Παπαδόπουλος", "Αντωνίου", "Κωνσταντίνου", "Δημητρίου", "Γεωργίου",
    "Ιωάννου", "Μιχαηλίδης", "Νικολάου", "Αναστασίου", "Χατζή",
    "Οικονόμου", "Βλάχος", "Σταματίου", "Θεοδώρου",
]
STREETS = [
    "Αθηνάς", "Σταδίου", "Πανεπιστημίου", "Ερμού", "Σόλωνος",
    "Πατησίων", "Αγίου Κωνσταντίνου", "Κηφισίας", "Βασιλίσσης Σοφίας",
    "Μιχαλακοπούλου", "Τσιμισκή", "Εγνατία", "Αριστοτέλους",
]
CITIES = [
    ("Αθήνα", (10431, 17675)), ("Θεσσαλονίκη", (54621, 57001)),
    ("Πάτρα", (26221, 26500)), ("Ηράκλειο", (70100, 71500)),
    ("Λάρισα", (41221, 41500)), ("Βόλος", (38221, 38500)),
    ("Ιωάννινα", (45221, 45500)), ("Τρίκαλα", (42100, 42200)),
]
DOMAINS = ["gmail.com", "yahoo.gr", "hotmail.com", "outlook.com",
           "forthnet.gr", "otenet.gr"]
URL_PATHS = [
    "instagram.com/{slug}", "twitter.com/{slug}", "github.com/{slug}",
    "linkedin.com/in/{slug}", "facebook.com/{slug}",
]


def _greek_slug(rng: random.Random, name: str) -> str:
    base = name.lower()
    return base + str(rng.randint(10, 99))


def gen_person(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(SURNAMES)}"


def gen_amka(rng: random.Random) -> str:
    # 11 digits: DDMMYY + 5 digits
    day = rng.randint(1, 28)
    mon = rng.randint(1, 12)
    yr = rng.randint(40, 99)
    suffix = f"{rng.randint(0, 99999):05d}"
    styles = [
        lambda: f"{day:02d}{mon:02d}{yr:02d}{suffix}",
        lambda: f"{day:02d}{mon:02d}{yr:02d}-{suffix}",
        lambda: f"{day:02d}{mon:02d}{yr:02d} {suffix}",
    ]
    return rng.choice(styles)()


def gen_afm(rng: random.Random) -> str:
    digits = f"{rng.randint(100000000, 999999999)}"
    styles = [
        lambda: digits,
        lambda: f"EL{digits}",
        lambda: f"Α.Φ.Μ.: {digits}",
        lambda: f"ΑΦΜ {digits}",
    ]
    return rng.choice(styles)()


def gen_adt(rng: random.Random) -> str:
    """Greek police ID: 2-3 uppercase Greek letters + 6 digits.

    The "Α.Δ.Τ." prefix is a LABEL that commonly appears in the
    surrounding text, not a part of the ID value itself. It must stay
    outside the labelled span so the model learns a consistent boundary.
    """
    greek_letters = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    letters = "".join(rng.choices(greek_letters, k=rng.choice([2, 3])))
    digits = f"{rng.randint(100000, 999999)}"
    styles = [
        lambda: f"{letters} {digits}",
        lambda: f"{letters}-{digits}",
        lambda: f"{letters}{digits}",
    ]
    return rng.choice(styles)()


def gen_iban_gr(rng: random.Random) -> str:
    # GR + 2 check digits + 25 chars (compact length 27)
    body = f"{rng.randint(0, 99):02d}" + "".join(
        rng.choices(string.digits, k=23)
    )
    compact = f"GR{body}"
    styles = [
        lambda: compact,
        lambda: " ".join(compact[i:i + 4] for i in range(0, len(compact), 4)),
        lambda: "-".join(compact[i:i + 4] for i in range(0, len(compact), 4)),
    ]
    return rng.choice(styles)()


def gen_phone(rng: random.Random) -> str:
    prefix = rng.choice(["69", "21", "231", "241"])
    remaining = 10 - len(prefix)
    digits = prefix + "".join(rng.choices(string.digits, k=remaining))
    styles = [
        lambda: digits,
        lambda: f"{digits[:4]} {digits[4:7]} {digits[7:]}",
        lambda: f"+30 {digits}",
        lambda: f"{digits[:4]}.{digits[4:7]}.{digits[7:]}",
    ]
    return rng.choice(styles)()


def gen_email(rng: random.Random) -> str:
    first = rng.choice(FIRST_NAMES).lower()
    last = rng.choice(SURNAMES).lower()
    # Real Greek users overwhelmingly use Latin transliterated names in
    # emails (IDN mailbox-local Greek is rare). Default 80% Latin, 20%
    # Greek to keep both visible to the model.
    if rng.random() < 0.8:
        first = transliterate_greek(first)
        last = transliterate_greek(last)
    sep = rng.choice([".", "_", ""])
    suffix = rng.randint(1, 999)
    return f"{first}{sep}{last}{suffix}@{rng.choice(DOMAINS)}"


def _latin_slug(rng: random.Random, name: str) -> str:
    return transliterate_greek(name.lower()) + str(rng.randint(10, 99))


def gen_url(rng: random.Random) -> str:
    pattern = rng.choice(URL_PATHS)
    if rng.random() < 0.8:
        slug = _latin_slug(rng, rng.choice(FIRST_NAMES))
    else:
        slug = _greek_slug(rng, rng.choice(FIRST_NAMES))
    return pattern.format(slug=slug)


def gen_address(rng: random.Random) -> str:
    street = rng.choice(STREETS)
    number = rng.randint(1, 250)
    city, (zip_lo, zip_hi) = rng.choice(CITIES)
    zip_code = rng.randint(zip_lo, zip_hi)
    styles = [
        lambda: f"{street} {number}, {city} {zip_code}",
        lambda: f"{street} {number}, {zip_code} {city}",
        lambda: f"{street} {number} - {city}",
    ]
    return rng.choice(styles)()


def gen_date(rng: random.Random) -> str:
    day = rng.randint(1, 28)
    mon = rng.randint(1, 12)
    year = rng.randint(1960, 2024)
    styles = [
        lambda: f"{day:02d}/{mon:02d}/{year}",
        lambda: f"{day:02d}-{mon:02d}-{year}",
        lambda: f"{day} {rng.choice(['Ιαν','Φεβ','Μαρ','Απρ','Μαϊ','Ιουν','Ιουλ','Αυγ','Σεπ','Οκτ','Νοε','Δεκ'])} {year}",
        lambda: str(year),
    ]
    return rng.choice(styles)()


def gen_account_number(rng: random.Random) -> str:
    # Generic account number (non-IBAN), e.g. bank internal or order id
    length = rng.choice([10, 12, 14])
    return "".join(rng.choices(string.digits, k=length))


def gen_secret(rng: random.Random) -> str:
    chars = string.ascii_uppercase + string.digits
    length = rng.choice([16, 20, 24, 32])
    return "sk-" + "".join(rng.choices(chars, k=length))


PII_GENERATORS: dict[str, Callable[[random.Random], str]] = {
    "private_person": gen_person,
    "amka": gen_amka,
    "afm": gen_afm,
    "adt": gen_adt,
    "iban_gr": gen_iban_gr,
    "private_phone": gen_phone,
    "private_email": gen_email,
    "private_url": gen_url,
    "private_address": gen_address,
    "private_date": gen_date,
    "account_number": gen_account_number,
    "secret": gen_secret,
}


# ---------------------------------------------------------------------------
# Carrier-text strategies
# ---------------------------------------------------------------------------

# Default built-in template bank. These sentences are original prose
# written for this project and are released under the same license as
# the rest of this repository. They contain {slot_name} placeholders.
TEMPLATE_BANK: list[tuple[str, str, list[str]]] = [
    # (template, domain, slot_categories)
    ("Ο πελάτης {private_person} δήλωσε ΑΦΜ {afm} και ΑΜΚΑ {amka}.",
     "tax_docs", ["private_person", "afm", "amka"]),
    ("Στείλε το τιμολόγιο στο {private_email} και στείλε SMS στο {private_phone}.",
     "business_email", ["private_email", "private_phone"]),
    ("Πληρωμή σε IBAN {iban_gr} με αναφορά {account_number}.",
     "banking", ["iban_gr", "account_number"]),
    ("Αρχείο ταυτότητας: {adt}. Τηλέφωνο επικοινωνίας {private_phone}.",
     "public_service", ["adt", "private_phone"]),
    ("Διεύθυνση αποστολής: {private_address}. Παραλήπτης: {private_person}.",
     "food_delivery", ["private_address", "private_person"]),
    ("Η συνέντευξη είναι στις {private_date}. Στείλε βιογραφικό στο {private_email}.",
     "job_application", ["private_date", "private_email"]),
    ("Ακυρώθηκε η κράτηση του {private_person} (ΑΜΚΑ {amka}) στις {private_date}.",
     "medical", ["private_person", "amka", "private_date"]),
    ("Για λεπτομέρειες επισκεφθείτε {private_url} ή στείλτε email στο {private_email}.",
     "forums", ["private_url", "private_email"]),
    ("Η πρόσβαση στο API γίνεται με το κλειδί {secret}. Μην το κοινοποιείς.",
     "code_comments", ["secret"]),
    ("Τρέχοντος μισθού: κατατίθεται στον IBAN {iban_gr} από την εταιρεία.",
     "hr", ["iban_gr"]),
    ("Παλιά διεύθυνση: {private_address}. Νέα διεύθυνση: {private_address}.",
     "rental", ["private_address", "private_address"]),
    # Hard-negative template: looks like PII but is just public info
    ("Δημοσιεύθηκε από τον δημοσιογράφο {private_person} στο περιοδικό.",
     "press", ["private_person"]),
]


# Hard-negative text that SHOULD NOT be labeled as PII (public entities,
# common nouns that look name-shaped, etc.)
HARD_NEGATIVE_TEMPLATES: list[str] = [
    "Η εταιρεία OpenAI ανακοίνωσε νέα προϊόντα AI στο Σαν Φρανσίσκο.",
    "Το Αριστοτέλειο Πανεπιστήμιο Θεσσαλονίκης ιδρύθηκε το 1925.",
    "Ο Δήμος Αθηναίων δημοσίευσε την ετήσια έκθεση πεπραγμένων.",
    "Η Ευρωπαϊκή Ένωση ενέκρινε νέο κανονισμό GDPR.",
    "Ο κωδικός σφάλματος HTTP 404 σημαίνει ότι η σελίδα δεν βρέθηκε.",
    "Ο όρος IBAN αναφέρεται στον διεθνή αριθμό τραπεζικού λογαριασμού.",
    "Το Σύνταγμα της Ελλάδας ψηφίστηκε το 1975.",
    "Η Ελληνική Στατιστική Αρχή δημοσίευσε νέα στοιχεία για το ΑΕΠ.",
]


def _load_carrier_sentences(path: Path) -> list[str]:
    sentences: list[str] = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get("text") or obj.get("sentence") or ""
            except json.JSONDecodeError:
                text = line
            if text:
                sentences.append(text)
    return sentences


_FEW_SHOT_HEADER = (
    "Παραδείγματα προτύπων προτάσεων. Κάθε πρόταση είναι ένα παράδειγμα "
    "φυσικής Ελληνικής με κενά πεδία σε μορφή {slot_N}, όπου κάθε slot "
    "σημαδεύει σημείο όπου θα εισαχθεί προσωπικό δεδομένο.\n\n"
)


def _format_few_shot_block(seed_examples: list[dict], rng: random.Random,
                           k: int = 4) -> str:
    """Render up to k seed examples as slot-template lines for the prompt.

    Each seed example is expected to have `text` and `label` fields in the
    project's JSONL schema. The function rewrites each labelled span into
    a {slot_N} placeholder so Meltemi learns the output shape.
    """
    if not seed_examples:
        return ""
    sample = rng.sample(seed_examples, k=min(k, len(seed_examples)))
    rendered: list[str] = []
    for ex in sample:
        text = ex["text"]
        spans = sorted(ex.get("label") or [], key=lambda s: s["start"])
        if not spans:
            rendered.append(f"- {text}")
            continue
        out = []
        cursor = 0
        for i, sp in enumerate(spans):
            out.append(text[cursor:sp["start"]])
            out.append(f"{{slot_{i}}}")
            cursor = sp["end"]
        out.append(text[cursor:])
        rendered.append(f"- {''.join(out)}")
    return _FEW_SHOT_HEADER + "\n".join(rendered) + "\n\n"


_SYSTEM_PROMPT = (
    "Είσαι βοηθός που γράφει σύντομες ελληνικές προτάσεις-πρότυπα για "
    "παραγωγή συνθετικών δεδομένων. ΔΕΝ απαντάς με διάλογο. Επιστρέφεις "
    "ΜΟΝΟ την πρόταση, χωρίς εισαγωγή, χωρίς εξήγηση, χωρίς εισαγωγικά, "
    "χωρίς παύλα στην αρχή."
)

_GREEK_CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "private_person": "ονοματεπώνυμο",
    "private_phone": "τηλέφωνο",
    "private_email": "email",
    "private_url": "σύνδεσμος",
    "private_address": "διεύθυνση",
    "private_date": "ημερομηνία",
    "account_number": "αριθμός λογαριασμού",
    "secret": "API key",
    "afm": "ΑΦΜ",
    "amka": "ΑΜΚΑ",
    "adt": "αριθμός ταυτότητας",
    "iban_gr": "IBAN",
}


_BATCH_REGISTERS: list[tuple[str, str]] = [
    (
        "επίσημο έγγραφο",
        "σύντομες προτάσεις όπως εμφανίζονται σε επίσημα έγγραφα ή "
        "φόρμες (π.χ. «Κατά την υποβολή της αίτησης, ο ενδιαφερόμενος "
        "δήλωσε …»).",
    ),
    (
        "business email",
        "σύντομες προτάσεις από επαγγελματικό email (π.χ. «Καλημέρα κ. "
        "Ιωάννου, παρακαλώ όπως μας αποστείλετε …»).",
    ),
    (
        "SMS / chat",
        "σύντομα μηνύματα SMS ή chat, άτυπα, ενδεχομένως χωρίς πλήρη "
        "σημεία στίξης (π.χ. «βρε στείλε μου το ΑΦΜ σου να το βάλω …»).",
    ),
    (
        "απομαγνητοφώνηση τηλεφωνικής κλήσης",
        "σύντομες ατάκες που θα άκουγες σε τηλεφωνική κλήση εξυπηρέτησης "
        "πελατών (π.χ. «Γειά σας, είμαι ο …, το ΑΦΜ μου είναι …»).",
    ),
    (
        "voicemail",
        "σύντομα μηνύματα τηλεφωνητή (π.χ. «Γεια σας, είμαι ο … από την "
        "εταιρεία …, καλέστε με στο …»).",
    ),
    (
        "προσωπική σημείωση",
        "σημειώσεις σε ημερολόγιο ή σε εφαρμογή notes (π.χ. «IBAN Γιάννη "
        "για ενοίκιο: …»).",
    ),
    (
        "ιατρική αναφορά",
        "παρατηρήσεις ιατρικού φακέλου ή δελτίο ραντεβού.",
    ),
    (
        "τραπεζικό μήνυμα",
        "ειδοποίηση από τράπεζα, e-banking ή push-notification.",
    ),
    (
        "HR επιστολή",
        "φράσεις από HR έγγραφο, βεβαίωση εργοδότη, συμβόλαιο εργασίας.",
    ),
    (
        "κρατική φόρμα",
        "αποσπάσματα από αιτήσεις, βεβαιώσεις, ή έντυπα δημοσίων "
        "υπηρεσιών.",
    ),
    (
        "support ticket",
        "σύντομο παράπονο ή αίτημα πελάτη προς τμήμα υποστήριξης.",
    ),
    (
        "social media post",
        "δημόσια ανάρτηση σε Facebook / Instagram / X / LinkedIn.",
    ),
]


_WRAPPER_LEADERS = (
    "Παράδειγμα:", "Παράδειγμα", "Σίγουρα!", "Φυσικά!", "Βεβαίως!",
    "Συγχαρητήρια!", "Ορίστε:", "Ιδού:", "Εδώ είναι:", "Ναι!",
    "Ένα παράδειγμα πρότασης είναι:", "Ένα παράδειγμα είναι:",
)


def _strip_meltemi_wrappers(content: str) -> str:
    """Remove common chat-model wrapper artefacts from a Meltemi response."""
    content = content.strip()
    # Drop any leading wrapper lines until we reach a line that contains {slot_.
    lines = content.splitlines()
    while lines:
        first = lines[0].strip()
        if not first or any(first.startswith(p) for p in _WRAPPER_LEADERS):
            lines.pop(0)
            continue
        break
    content = "\n".join(lines).strip()
    # Drop leading bullet/dash/quote.
    for prefix in ("- ", "• ", "— ", "* ", "\"", "«", "'", "`"):
        if content.startswith(prefix):
            content = content[len(prefix):]
            content = content.lstrip()
    for suffix in ("\"", "»", "'", "`"):
        if content.endswith(suffix):
            content = content[: -len(suffix)]
    # Take only the first paragraph/line to avoid multi-sentence rambles.
    content = content.split("\n", 1)[0].strip()
    return content


def _ollama_generate_carrier(model: str, host: str, rng: random.Random,
                             categories: list[str],
                             seed_examples: list[dict] | None = None) -> str:
    """Ask a locally running Ollama chat model for one slot-templated sentence.

    The caller picks the exact PII categories to inject and passes them in
    `categories`; the prompt spells out to Meltemi which slot corresponds
    to which category so the generated context matches the category
    semantically (e.g. asking for a phone slot will produce "κάλεσέ με
    στο {slot_0}" rather than "η διεύθυνση είναι {slot_0}").

    Uses `/api/chat` so Ollama applies Meltemi's native chat template.
    """
    import json as _json
    import urllib.request

    seed_block = _format_few_shot_block(seed_examples or [], rng)
    slot_spec_lines = [
        f"- {{slot_{i}}} = {_GREEK_CATEGORY_DESCRIPTIONS.get(cat, cat)}"
        for i, cat in enumerate(categories)
    ]
    slot_spec = "\n".join(slot_spec_lines)

    user_msg = (
        f"{seed_block}"
        "Γράψε ΜΙΑ σύντομη, φυσική ελληνική πρόταση που να περιέχει "
        f"ακριβώς {len(categories)} κενά πεδία σε μορφή {{slot_0}}, "
        "{slot_1}, ... Η ΣΗΜΑΣΙΟΛΟΓΙΚΗ ΘΕΣΗ κάθε slot πρέπει να ταιριάζει "
        "με τον τύπο δεδομένων που αναφέρεται παρακάτω:\n\n"
        f"{slot_spec}\n\n"
        "Η πρόταση να είναι ρεαλιστική (π.χ. εμπορική, διοικητική, "
        "ιατρική, τραπεζική, email, chat) και να μπαίνει το κάθε slot "
        "σε κατάλληλο πλαίσιο. ΜΗΝ γράφεις τα ονόματα των τύπων στον "
        "τελικό λόγο (π.χ. γράψε «Η διεύθυνση είναι {slot_0}» και όχι "
        "«Η διεύθυνση {slot_0}»). Επέστρεψε ΜΟΝΟ την πρόταση, χωρίς "
        "εισαγωγή ή εξήγηση, χωρίς εισαγωγικά, χωρίς παύλα στην αρχή."
    )

    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=_json.dumps({
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "options": {"temperature": 0.8, "seed": rng.randint(0, 2**31 - 1)},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = _json.loads(resp.read().decode("utf-8"))
    content = payload.get("message", {}).get("content", "")
    return _strip_meltemi_wrappers(content)


# ---------------------------------------------------------------------------
# Example builders
# ---------------------------------------------------------------------------

def _render_template(
    template: str, slot_categories: list[str], rng: random.Random
) -> dict:
    # Build substitutions and emit final text + spans.
    out_text = ""
    spans: list[dict] = []
    cursor = 0
    slot_iter = iter(slot_categories)
    pattern = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    last_end = 0
    for m in pattern.finditer(template):
        slot_name = m.group(1)
        # Treat any placeholder matching a PII category as a PII slot.
        if slot_name in PII_GENERATORS:
            category = slot_name
        else:
            # If a numbered placeholder like slot_0 is used, pull next
            # category from slot_categories (by position).
            try:
                category = next(slot_iter)
            except StopIteration:
                category = "private_person"
        value = PII_GENERATORS[category](rng)
        # Append literal prefix.
        out_text += template[last_end:m.start()]
        span_start = len(out_text)
        out_text += value
        span_end = len(out_text)
        spans.append(
            {"category": category, "start": span_start, "end": span_end}
        )
        last_end = m.end()
    out_text += template[last_end:]

    return {"text": out_text, "label": spans}


def _build_from_template(
    rng: random.Random, difficulty: str = "easy"
) -> dict:
    template, domain, slot_categories = rng.choice(TEMPLATE_BANK)
    sample = _render_template(template, slot_categories, rng)
    sample["info"] = {
        "difficulty": difficulty,
        "domain": domain,
        "source": "commercial_safe_generator",
        "strategy": "templates",
    }
    return sample


def _build_hard_negative(rng: random.Random) -> dict:
    text = rng.choice(HARD_NEGATIVE_TEMPLATES)
    return {
        "text": text,
        "label": [],
        "info": {
            "difficulty": "hard_negative",
            "domain": "hard_negative",
            "source": "commercial_safe_generator",
            "strategy": "hard_negative",
        },
    }


def _build_from_carrier(
    carrier_sentences: list[str], rng: random.Random
) -> dict:
    """Take a carrier sentence (from CC0/public-domain corpus) and inject PII."""
    carrier = rng.choice(carrier_sentences).rstrip()
    # Pick 1-3 PII types to append to the carrier as a natural continuation.
    categories = rng.sample(list(PII_GENERATORS), k=rng.randint(1, 3))
    pieces: list[str] = [carrier]
    spans: list[dict] = []
    cursor = len(carrier)
    for category in categories:
        value = PII_GENERATORS[category](rng)
        intro = rng.choice([
            " Στοιχεία: ", " - ", ". Επικοινωνία: ", ". Αναφορά: ",
        ])
        pieces.append(intro)
        cursor += len(intro)
        spans.append(
            {"category": category, "start": cursor, "end": cursor + len(value)}
        )
        pieces.append(value)
        cursor += len(value)
    return {
        "text": "".join(pieces),
        "label": spans,
        "info": {
            "difficulty": "medium",
            "domain": "carrier_inject",
            "source": "commercial_safe_generator",
            "strategy": "carrier",
        },
    }


def _ollama_batch_chat(model: str, host: str, system_prompt: str,
                       user_prompt: str, temperature: float, seed: int,
                       engine: str = "ollama",
                       max_tokens: int = 2048,
                       timeout: float = 300.0) -> str:
    """Single chat-completion call returning the assistant content string.

    Supports two backends with the same JSON schema:
      * ollama    → POST {host}/api/chat
      * openai    → POST {host}/v1/chat/completions (llama-server, vLLM,
                    OpenAI, Together, etc.)
    """
    import json as _json
    import urllib.request
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    if engine == "openai":
        url = f"{host.rstrip('/')}/v1/chat/completions"
        body = {
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_tokens,
            # llama-server / vLLM forward chat_template_kwargs to the
            # tokenizer chat template. For Qwen3.x-thinking models this
            # suppresses the <think>...</think> reasoning block, which
            # would otherwise swallow the entire token budget.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if model:
            body["model"] = model
    else:
        url = f"{host.rstrip('/')}/api/chat"
        body = {
            "model": model,
            "stream": False,
            "messages": messages,
            "options": {"temperature": temperature, "seed": seed},
        }
    req = urllib.request.Request(
        url,
        data=_json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = _json.loads(resp.read().decode("utf-8"))
    if engine == "openai":
        choices = payload.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")
    return payload.get("message", {}).get("content", "")


_NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)[.\)]\s*(.+?)\s*$")


def _build_batch_from_ollama(
    rng: random.Random, model: str, host: str,
    batch_size: int = 10, engine: str = "ollama",
) -> list[dict]:
    """Ask the LLM to write N numbered Greek sentences embedding specific
    PII values.

    Each numbered item may carry 1, 2, or 3 (category, value) pairs — the
    LLM is asked to fit all of them into the same sentence so the
    dataset gets realistic multi-PII co-occurrence.

    A random register (phone-call transcript, SMS, business email,
    medical chart, etc.) is picked per batch so consecutive calls
    produce stylistically varied output rather than the same formal
    imperative tone.
    """
    items: list[list[tuple[str, str]]] = []
    weights = [0.5, 0.35, 0.15]  # 1 / 2 / 3 PII per item
    for _ in range(batch_size):
        k = rng.choices([1, 2, 3], weights=weights, k=1)[0]
        cats = rng.sample(list(PII_GENERATORS), k=min(k, len(PII_GENERATORS)))
        pairs = [(c, PII_GENERATORS[c](rng)) for c in cats]
        items.append(pairs)

    register_name, register_desc = rng.choice(_BATCH_REGISTERS)

    lines = []
    for i, pairs in enumerate(items, start=1):
        parts = [
            f"{_GREEK_CATEGORY_DESCRIPTIONS.get(c, c)}: {v}"
            for c, v in pairs
        ]
        lines.append(f"{i}. " + "  +  ".join(parts))
    values_block = "\n".join(lines)

    user_prompt = (
        f"Ύφος: {register_name}.\n"
        f"Οδηγίες ύφους: {register_desc}\n\n"
        f"Γράψε ΑΚΡΙΒΩΣ {batch_size} σύντομες, φυσικές προτάσεις σε αυτό "
        "το ύφος. Κάθε αριθμημένη πρόταση πρέπει να περιέχει ΑΥΤΟΥΣΙΕΣ "
        "ΟΛΕΣ τις τιμές που αντιστοιχούν στον ίδιο αριθμό (αν είναι "
        "περισσότερες από μία, ενσωμάτωσέ τες όλες στην ίδια πρόταση).\n\n"
        f"Τιμές ανά πρόταση:\n{values_block}\n\n"
        "Κανόνες:\n"
        "- Οι τιμές να εμφανίζονται ΑΥΤΟΥΣΙΕΣ (ίδια κεφαλαία/πεζά, "
        "ίδιες παύλες, ίδια κενά).\n"
        "- ΜΗΝ χρησιμοποιείς τις ετικέτες «ΑΦΜ», «email», κ.λπ. αυτούσια "
        "ως πρόθεμα όταν δεν ταιριάζουν στη ροή της πρότασης — ενσωμάτωσε "
        "τις τιμές φυσικά στον λόγο.\n"
        "- Κάθε πρόταση σε ξεχωριστή γραμμή αριθμημένη «1.», «2.», ...\n"
        "- 6–24 λέξεις ανά πρόταση.\n"
        "- Χωρίς εισαγωγή, χωρίς επεξήγηση, χωρίς εισαγωγικά."
    )

    try:
        content = _ollama_batch_chat(
            model, host, _SYSTEM_PROMPT, user_prompt,
            temperature=0.8, seed=rng.randint(0, 2**31 - 1),
            engine=engine,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[llm batch] generation failed: {exc}")
        return []

    parsed: dict[int, str] = {}
    for line in content.splitlines():
        m = _NUMBERED_LINE_RE.match(line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        text = _strip_meltemi_wrappers(m.group(2))
        if 0 <= idx < batch_size and text and idx not in parsed:
            parsed[idx] = text

    out: list[dict] = []
    for idx, pairs in enumerate(items):
        text = parsed.get(idx)
        if not text:
            continue
        labels: list[dict] = []
        cursor = 0
        ok = True
        for category, value in pairs:
            pos = text.find(value, cursor)
            if pos < 0:
                # Try the whole string as a fallback — order-insensitive
                pos = text.find(value)
            if pos < 0:
                ok = False
                break
            labels.append(
                {"category": category, "start": pos, "end": pos + len(value)}
            )
            cursor = pos + len(value)
        if not ok or not labels:
            continue
        labels.sort(key=lambda sp: sp["start"])
        out.append({
            "text": text,
            "label": labels,
            "info": {
                "difficulty": "medium" if len(pairs) == 1 else "hard",
                "domain": f"llm_register:{register_name}",
                "source": "commercial_safe_generator",
                "strategy": f"llm-server/{model}/batch",
            },
        })
    return out


class _OllamaBatchQueue:
    """Amortises Meltemi calls over many draws.

    Each `pop()` returns one cached batch example; when the queue is
    empty, a new batch is fetched. Errors return None and the caller
    should fall back to a template/carrier sample.
    """

    def __init__(self, rng: random.Random, model: str, host: str,
                 batch_size: int = 10, engine: str = "ollama") -> None:
        self.rng = rng
        self.model = model
        self.host = host
        self.batch_size = batch_size
        self.engine = engine
        self._queue: list[dict] = []
        self.calls = 0
        self.accepted = 0
        self.requested = 0

    def pop(self) -> dict | None:
        if not self._queue:
            self.calls += 1
            self.requested += self.batch_size
            batch = _build_batch_from_ollama(
                self.rng, self.model, self.host, self.batch_size,
                engine=self.engine,
            )
            self.accepted += len(batch)
            self._queue.extend(batch)
        if self._queue:
            return self._queue.pop(0)
        return None


def _build_from_ollama(
    rng: random.Random, model: str, host: str,
    seed_examples: list[dict] | None = None,
) -> dict | None:
    """Legacy single-example slot-template generator. Kept for compatibility.

    For production runs, prefer the batched value-insertion path through
    `_OllamaBatchQueue`, which has a much higher semantic-match rate on
    small models like Meltemi-7B.
    """
    n_slots = rng.randint(1, 2)
    categories = rng.sample(list(PII_GENERATORS), k=n_slots)
    try:
        carrier = _ollama_generate_carrier(
            model, host, rng, categories, seed_examples
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ollama] generation failed: {exc}; falling back to template")
        return None
    slot_pattern = re.compile(r"\{slot_(\d+)\}")
    slot_indices = [int(m.group(1)) for m in slot_pattern.finditer(carrier)]
    if not slot_indices:
        return None
    slot_to_category = {
        idx: categories[i % len(categories)] for i, idx in enumerate(slot_indices)
    }
    out_text = ""
    spans: list[dict] = []
    last_end = 0
    for m in slot_pattern.finditer(carrier):
        idx = int(m.group(1))
        category = slot_to_category[idx]
        value = PII_GENERATORS[category](rng)
        out_text += carrier[last_end:m.start()]
        span_start = len(out_text)
        out_text += value
        span_end = len(out_text)
        spans.append(
            {"category": category, "start": span_start, "end": span_end}
        )
        last_end = m.end()
    out_text += carrier[last_end:]
    return {
        "text": out_text,
        "label": spans,
        "info": {
            "difficulty": "medium",
            "domain": "llm_carrier",
            "source": "commercial_safe_generator",
            "strategy": f"llm-server/{model}/slot",
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument(
        "--mode",
        choices=("templates", "carrier", "ollama", "mix"),
        default="mix",
        help="Which carrier strategy to use. 'mix' interleaves templates "
             "and hard negatives in a ~80/20 ratio.",
    )
    parser.add_argument(
        "--hard-negative-ratio", type=float, default=0.2,
        help="Fraction of output examples that should be hard negatives.",
    )
    parser.add_argument(
        "--carrier-jsonl", type=str, default=None,
        help="Path to a JSONL of CC0/public-domain Greek sentences "
             "(field 'text' or 'sentence'). Used when --mode=carrier|mix.",
    )
    parser.add_argument(
        "--ollama-model", default="unsloth/Qwen3.6-35B-A3B-GGUF",
        help="LLM model identifier used as the per-record provenance "
             "label (info.strategy). Defaults to the Qwen3.6-35B-A3B "
             "GGUF served by llama-server. The original argument name "
             "is preserved for backward compatibility — the underlying "
             "transport is OpenAI-compatible HTTP, not Ollama.",
    )
    parser.add_argument("--ollama-host", default="http://localhost:11434")
    parser.add_argument(
        "--few-shot-file", type=str, default=None,
        help="Optional path to a JSONL of golden seed examples (same "
             "schema as output). Used only by the legacy slot-template "
             "path (--ollama-mode=slot).",
    )
    parser.add_argument(
        "--ollama-mode", choices=("batch", "slot"), default="batch",
        help="Meltemi generation strategy. 'batch' (default) asks "
             "Meltemi to write N numbered sentences around PII values we "
             "author — best semantic match rate. 'slot' is the legacy "
             "fill-in-the-blank flow (slower + lower quality on 7B models).",
    )
    parser.add_argument(
        "--ollama-batch-size", type=int, default=10,
        help="How many numbered sentences to request per Meltemi call "
             "when --ollama-mode=batch.",
    )
    parser.add_argument(
        "--ollama-fraction", type=float, default=0.5,
        help="Share of positive examples drawn from Meltemi when --mode "
             "includes ollama. Rest fall back to templates/carrier.",
    )
    parser.add_argument(
        "--llm-engine", choices=("ollama", "openai"), default="ollama",
        help="'ollama' uses {host}/api/chat; 'openai' uses "
             "{host}/v1/chat/completions (llama-server, vLLM, OpenAI-compat).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    carrier_sentences: list[str] = []
    if args.carrier_jsonl:
        carrier_path = Path(args.carrier_jsonl).expanduser()
        if not carrier_path.is_absolute():
            carrier_path = PROJECT_ROOT / carrier_path
        carrier_sentences = _load_carrier_sentences(carrier_path)
        print(f"Loaded {len(carrier_sentences)} carrier sentences from "
              f"{carrier_path}")

    seed_examples: list[dict] = []
    if args.few_shot_file:
        seed_path = Path(args.few_shot_file).expanduser()
        if not seed_path.is_absolute():
            seed_path = PROJECT_ROOT / seed_path
        with seed_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                seed_examples.append(json.loads(line))
        print(f"Loaded {len(seed_examples)} few-shot seed examples from "
              f"{seed_path}")

    hard_negative_target = int(args.count * args.hard_negative_ratio)
    positive_target = args.count - hard_negative_target

    ollama_queue: _OllamaBatchQueue | None = None
    if args.mode in ("ollama", "mix") and args.ollama_mode == "batch":
        ollama_queue = _OllamaBatchQueue(
            rng, args.ollama_model, args.ollama_host,
            batch_size=max(1, args.ollama_batch_size),
            engine=args.llm_engine,
        )

    n_written = 0
    with output_path.open("w", encoding="utf-8") as out_fp:
        # Hard negatives first (they're cheap and we don't want to skip them).
        for _ in range(hard_negative_target):
            sample = _build_hard_negative(rng)
            out_fp.write(json.dumps(sample, ensure_ascii=False) + "\n")
            n_written += 1

        for _ in range(positive_target):
            sample = None
            want_ollama = (
                args.mode in ("ollama", "mix")
                and rng.random() < args.ollama_fraction
            )
            if want_ollama:
                if ollama_queue is not None:
                    sample = ollama_queue.pop()
                else:
                    sample = _build_from_ollama(
                        rng, args.ollama_model, args.ollama_host,
                        seed_examples=seed_examples or None,
                    )
            if sample is None and args.mode in ("carrier", "mix") \
                    and carrier_sentences and rng.random() < 0.5:
                sample = _build_from_carrier(carrier_sentences, rng)
            if sample is None:
                # Fall back to template (always safe; no external deps).
                difficulty = rng.choices(
                    ["easy", "medium", "hard"], weights=[0.4, 0.4, 0.2]
                )[0]
                sample = _build_from_template(rng, difficulty=difficulty)
            out_fp.write(json.dumps(sample, ensure_ascii=False) + "\n")
            n_written += 1

    if ollama_queue is not None:
        acceptance = (
            (ollama_queue.accepted / ollama_queue.requested * 100)
            if ollama_queue.requested else 0.0
        )
        print(
            f"[ollama batch] {ollama_queue.calls} calls, "
            f"{ollama_queue.accepted}/{ollama_queue.requested} accepted "
            f"({acceptance:.1f}%)"
        )

    # Final sanity check: every span offset must be non-empty.
    bad = 0
    with output_path.open("r", encoding="utf-8") as fp:
        for line in fp:
            d = json.loads(line)
            for sp in d.get("label") or []:
                if not d["text"][sp["start"]:sp["end"]]:
                    bad += 1
    print(f"Wrote {n_written} examples to {output_path} (bad offsets: {bad})")


if __name__ == "__main__":
    main()
