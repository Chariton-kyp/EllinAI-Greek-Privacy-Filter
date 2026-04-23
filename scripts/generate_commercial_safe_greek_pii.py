"""Generate Greek PII training data that is 100% commercially usable.

This generator produces labeled examples where:

  * Carrier text (the sentence surrounding the PII) comes from either:
      - public-domain / CC0 sources (PleIAs/Greek-PD, Mozilla Common Voice
        Greek text), which the user passes in via --carrier-jsonl, or
      - locally-running open-weight LLMs via Ollama (Llama 3, Mistral,
        Gemma), which the user fully owns the outputs of, or
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

With an open-weight local model via Ollama:

  ollama pull llama3.1:8b
  python scripts/generate_commercial_safe_greek_pii.py \
      --output data/processed/greek_commercial_safe.jsonl \
      --count 2000 --mode ollama --ollama-model llama3.1:8b

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
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    greek_letters = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    letters = "".join(rng.choices(greek_letters, k=rng.choice([2, 3])))
    digits = f"{rng.randint(100000, 999999)}"
    styles = [
        lambda: f"{letters} {digits}",
        lambda: f"{letters}-{digits}",
        lambda: f"{letters}{digits}",
        lambda: f"Α.Δ.Τ. {letters} {digits}",
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
    sep = rng.choice([".", "_", ""])
    suffix = rng.randint(1, 999)
    return f"{first}{sep}{last}{suffix}@{rng.choice(DOMAINS)}"


def gen_url(rng: random.Random) -> str:
    pattern = rng.choice(URL_PATHS)
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


def _ollama_generate_carrier(model: str, host: str, rng: random.Random) -> str:
    """Ask a locally running Ollama model to produce one neutral Greek sentence.

    The model is asked to produce a sentence WITHOUT any PII; we inject PII
    ourselves in a second step so we always know the gold-standard spans.
    """
    import json as _json
    import urllib.request

    prompt = (
        "Γράψε ΕΝΑ φυσικό, καθημερινό Ελληνικό πρότυπο πρόταση, χωρίς "
        "προσωπικά δεδομένα (χωρίς ονόματα, αριθμούς, email). Άφησε τα σημεία "
        "όπου θα μπορούσαν να μπουν προσωπικά δεδομένα ως {slot_0}, {slot_1}, "
        "... Επέστρεψε ΜΟΝΟ την πρόταση, χωρίς εισαγωγή ή εξήγηση."
    )
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=_json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.8, "seed": rng.randint(0, 2**31 - 1)},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = _json.loads(resp.read().decode("utf-8"))
    return payload.get("response", "").strip()


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


def _build_from_ollama(
    rng: random.Random, model: str, host: str
) -> dict | None:
    try:
        carrier = _ollama_generate_carrier(model, host, rng)
    except Exception as exc:  # noqa: BLE001
        print(f"[ollama] generation failed: {exc}; falling back to template")
        return None
    # Replace numbered slots with PII categories.
    slot_pattern = re.compile(r"\{slot_(\d+)\}")
    slot_indices = [int(m.group(1)) for m in slot_pattern.finditer(carrier)]
    if not slot_indices:
        # Model ignored the instruction; fall back to template.
        return None
    categories = rng.sample(
        list(PII_GENERATORS), k=min(len(slot_indices), len(PII_GENERATORS))
    )
    # Map each slot index to a category.
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
            "strategy": f"ollama/{model}",
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
    parser.add_argument("--ollama-model", default="llama3.1:8b")
    parser.add_argument("--ollama-host", default="http://localhost:11434")
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

    hard_negative_target = int(args.count * args.hard_negative_ratio)
    positive_target = args.count - hard_negative_target

    n_written = 0
    with output_path.open("w", encoding="utf-8") as out_fp:
        # Hard negatives first (they're cheap and we don't want to skip them).
        for _ in range(hard_negative_target):
            sample = _build_hard_negative(rng)
            out_fp.write(json.dumps(sample, ensure_ascii=False) + "\n")
            n_written += 1

        for _ in range(positive_target):
            sample = None
            if args.mode in ("ollama", "mix") and rng.random() < 0.3:
                sample = _build_from_ollama(rng, args.ollama_model, args.ollama_host)
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
