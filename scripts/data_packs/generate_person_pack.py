"""Generate v2.5 person-inflection pack.

Produces JSONL records of Greek prose containing inflected person names
embedded in realistic carrier sentences. Targets the v2 model's biggest
real-world weakness: 63 missed names + 17 boundary errors out of 144
expected names in the OOD benchmark (44% miss rate).

Each record has:
    text — natural Greek prose
    spans — list of {label="private_person", text, start, end}

Usage:
    python scripts/data_packs/generate_person_pack.py \\
        --output data/processed/person_pack.jsonl \\
        --count 15000 \\
        --seed 1337
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "data_packs"))

from greek_names import compose_name


# Carrier templates — each has {NAME} placeholder. Templates cover
# different syntactic positions: subject, object, possessor, vocative,
# titled. Designed to test boundary detection across positions.

CARRIER_TEMPLATES = [
    # Subject position (nominative-friendly)
    "Ο {NAME} ολοκλήρωσε τη διαδικασία.",
    "Η {NAME} κατέθεσε την αίτηση χθες.",
    "{NAME} είναι υπεύθυνος για το έργο.",
    "Στο γραφείο μας εργάζεται ο {NAME}.",
    "Ο {NAME} ηγείται της ομάδας ανάπτυξης.",
    "Η {NAME} έλαβε τη βεβαίωση σπουδών.",
    "Σήμερα συναντήθηκα με τον {NAME}.",
    "{NAME} συμμετείχε στο συνέδριο της Πέμπτης.",
    "Σύμφωνα με δηλώσεις του {NAME}, η εταιρεία επεκτείνεται.",
    "Η εκπρόσωπος Τύπου {NAME} ανακοίνωσε νέα μέτρα.",
    # Object/possessor position (accusative/genitive-friendly)
    "Παρακαλώ προωθήστε το αίτημα στον {NAME}.",
    "Το έργο ανέλαβε η {NAME}.",
    "Η συμβολή του {NAME} ήταν καθοριστική.",
    "Η εταιρεία προσέλαβε τον {NAME} ως νέο διευθυντή.",
    "Από τον {NAME} έλαβα όλες τις πληροφορίες.",
    "Στείλτε αντίγραφο και στην {NAME}.",
    "Με την υπογραφή του {NAME} εγκρίθηκε η αίτηση.",
    "Τα έγγραφα παραδίδονται μόνο στην {NAME}.",
    "Επικοινωνήστε με τον {NAME} για λεπτομέρειες.",
    "Ο φάκελος ανήκει στην {NAME}.",
    # Vocative position
    "Αξιότιμε {NAME},",
    "Αγαπητή {NAME},",
    "Αγαπητέ μας {NAME}, σας ευχαριστούμε.",
    "Καλημέρα, {NAME}!",
    "Γεια σου {NAME}, πώς πάει;",
    "Προς τον {NAME},",
    "Κύριε {NAME}, παρακαλώ προσέλθετε.",
    "Κυρία {NAME}, σας περιμένουμε.",
    # Formal letter / report
    "Με την παρούσα ενημερώνουμε τον {NAME} ότι η αίτησή του παρελήφθη.",
    "Η ομιλία του {NAME} έγινε ιδιαίτερα δεκτή από το ακροατήριο.",
    "Η αναφορά αφορά τον υπάλληλο {NAME}.",
    "Ο/Η {NAME} ζητά ανανέωση της σύμβασης.",
    "Με εντολή του προέδρου {NAME}, εκδίδεται η παρούσα.",
    "Σύμφωνα με το συμβόλαιο που υπέγραψε ο/η {NAME}, ισχύει η ρήτρα 4.2.",
    "Η ενορχηστρώτρια {NAME} προσφέρει την υπογραφή της.",
    "Με σεβασμό, {NAME}, τμήμα ανθρώπινου δυναμικού.",
    # Multi-paragraph contexts
    "Η συνέντευξη του {NAME} δημοσιεύτηκε στην εβδομαδιαία έκδοση.",
    "Οι ερευνητές, μεταξύ των οποίων ο/η {NAME}, δημοσίευσαν τα ευρήματα.",
    "Η μαρτυρία της {NAME} είναι κρίσιμη για την υπόθεση.",
    "Ο διοικητής {NAME} επιθεώρησε τις εγκαταστάσεις.",
    "Σχετικά με το αίτημα του {NAME}, εκκρεμεί απάντηση.",
    "Η συμμετοχή της {NAME} κρίθηκε εξαιρετική.",
    # SMS / informal
    "Πες στον {NAME} να με πάρει.",
    "Ο {NAME} σου άφησε μήνυμα.",
    "Πρέπει να μιλήσω με την {NAME} άμεσα.",
    "Δωσ' το στον {NAME} αν τον δεις.",
    # Multi-name templates (split into two name pickers)
    "Παρόντες ήταν ο/η {NAME1} και η {NAME2}.",
    "Από κοινού οι {NAME1} και {NAME2} προχώρησαν στην υπογραφή.",
    "Ο {NAME1} αντικαθιστά τον {NAME2} στο τμήμα.",
    "Η συνεργασία μεταξύ {NAME1} και {NAME2} ήταν παραγωγική.",
]

# Templates that need TWO independent names
TWO_NAME_TEMPLATES = [
    t for t in CARRIER_TEMPLATES if "{NAME1}" in t and "{NAME2}" in t
]
SINGLE_NAME_TEMPLATES = [t for t in CARRIER_TEMPLATES if t not in TWO_NAME_TEMPLATES]


def generate_record(rng: random.Random) -> dict:
    """Generate one person-pack record (v1.1-compatible schema)."""
    if rng.random() < 0.15 and TWO_NAME_TEMPLATES:
        template = rng.choice(TWO_NAME_TEMPLATES)
        n1 = compose_name(rng)
        n2 = compose_name(rng)
        text = template.replace("{NAME1}", n1.text).replace("{NAME2}", n2.text)
        labels = []
        cursor = 0
        for nm in (n1, n2):
            idx = text.find(nm.text, cursor)
            if idx == -1:
                continue
            labels.append({"category": "private_person",
                           "start": idx, "end": idx + len(nm.text)})
            cursor = idx + len(nm.text)
    else:
        template = rng.choice(SINGLE_NAME_TEMPLATES)
        roll = rng.random()
        if roll < 0.05:
            n = compose_name(rng, first_only=True)
        elif roll < 0.10:
            n = compose_name(rng, last_only=True)
        elif roll < 0.20:
            n = compose_name(rng, last_first_order=True)
        elif roll < 0.30:
            n = compose_name(rng, include_title=True)
        else:
            n = compose_name(rng)
        text = template.replace("{NAME}", n.text)
        idx = text.find(n.text)
        labels = [{"category": "private_person",
                   "start": idx, "end": idx + len(n.text)}]
    return {"text": text, "label": labels,
            "info": {"source": "v2_5_person_pack", "domain": "carrier_template"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=15000)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(args.output, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            rec = generate_record(rng)
            ok = True
            for lab in rec["label"]:
                seg = rec["text"][lab["start"]:lab["end"]]
                if not seg or len(seg) == 0:
                    ok = False
                    break
            if not ok:
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written} person-pack records to {args.output}")


if __name__ == "__main__":
    main()
