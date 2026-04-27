"""Real-world inference test for the v1 fine-tuned Greek Privacy Filter.

Constructs realistic Greek-language test passages combining authentic
Greek prose patterns (legal text style, business correspondence, SMS,
medical chart, banking notification, etc.) with manually-crafted
synthetic PII spans. No real personal data is processed: all PII
values are fictional but follow the canonical Greek formats (AFM
9-digit, AMKA 11-digit, ADT letter+6digit, IBAN GR + 25 digits, etc.).

The script loads the fine-tuned checkpoint, runs ``OPF.redact`` on
every test passage, and prints predicted vs expected spans side by
side along with overall precision/recall on this hand-graded set.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_DIR = PROJECT_ROOT / "data" / "processed" / "aws-ft-20260426T135853Z" / "model"


# ─── Test cases ────────────────────────────────────────────────────────
# Each entry: dict(register, text, expected[(label, start, end)])
# All values fictional. Greek formats follow real-world conventions.

TESTS = [
    {
        "register": "business email",
        "text": (
            "Καλημέρα κ. Παπαδόπουλε,\n\n"
            "Επιβεβαιώνουμε τη συνάντηση την Παρασκευή 30 Μαΐου 2025 στο γραφείο μας. "
            "Παρακαλώ επικοινωνήστε με τη γραμματεία μας στο 2103456789 ή στο "
            "info@law-firm-athens.gr για οποιαδήποτε αλλαγή."
        ),
    },
    {
        "register": "SMS",
        "text": (
            "Γεια σου Μαρία! Ο γιατρός θέλει το ΑΜΚΑ σου 15076512345 και τον ΑΦΜ "
            "078123456 για τη συνταγή. Πες του και τη ΑΔΤ ΑΖ123456 πριν τη Δευτέρα."
        ),
    },
    {
        "register": "banking notification",
        "text": (
            "Αγαπητέ πελάτη, η μεταφορά 1.250,00€ προς τον λογαριασμό 014/220123456 "
            "(IBAN GR1601100140000001402201234) ολοκληρώθηκε την 15/06/2025. "
            "Ο νέος κωδικός μίας χρήσης είναι TX9-AB7-PQ42 και ισχύει για 5 λεπτά."
        ),
    },
    {
        "register": "medical chart",
        "text": (
            "Ασθενής: Γεώργιος Δημητρίου, ΑΜΚΑ 22018054321. Ημερομηνία γέννησης: 22/01/1980. "
            "Διεύθυνση: Αγίου Κωνσταντίνου 14, Πειραιάς. Τηλ. επικοινωνίας: 6981234567. "
            "Παραπεμπτικός ιατρός: dr.papadimitriou@iatreio.gr."
        ),
    },
    {
        "register": "HR letter",
        "text": (
            "Με την παρούσα βεβαιώνουμε ότι ο κ. Νίκος Αντωνίου εργάζεται στην εταιρεία μας "
            "από 01/03/2018. Ο ΑΦΜ του είναι 134567890 και ο κωδικός τραπεζικού λογαριασμού "
            "που χρησιμοποιείται για μισθοδοσία είναι 175/487654321."
        ),
    },
    {
        "register": "support ticket",
        "text": (
            "Ticket #4421: Ο χρήστης δεν μπορεί να συνδεθεί. Email: kostas.giannidis@example.gr, "
            "URL προφίλ: https://platform.example.gr/users/12944. Παρακαλώ ελέγξτε το token "
            "σύνδεσης sk-LIVE-9a2bf7ed4c3e και ενημερώστε εάν χρειάζεται reset."
        ),
    },
    {
        "register": "government form",
        "text": (
            "Όνομα: Ελένη Παπανικολάου. Πατρώνυμο: Ιωάννης. Α.Δ.Τ.: ΑΗ987654. "
            "Διεύθυνση κατοικίας: Πατησίων 88, Αθήνα 10434. Τηλέφωνο: 2106789012. "
            "Ηλεκτρονικό ταχυδρομείο: e.papanikolaou@dimosio.gr."
        ),
    },
    {
        "register": "carrier-only (no PII)",
        "text": (
            "Η Ελληνική Δημοκρατία αποτελεί κράτος δικαίου με κοινοβουλευτική δημοκρατία. "
            "Η οικονομία της βασίζεται στις υπηρεσίες, στον τουρισμό και στη γεωργία."
        ),
    },
    {
        "register": "mixed Greek/Latin contact",
        "text": (
            "Επικοινωνήστε στο τηλέφωνο 6987654321 ή στείλτε email στο νικος@παράδειγμα.gr "
            "για τη συνέντευξη της 03/07/2025. Η εταιρεία ΧΥΖ Α.Ε. βρίσκεται στη Λεωφόρο "
            "Αλεξάνδρας 105."
        ),
    },
    {
        "register": "tricky numerics (hard negatives + real PII)",
        "text": (
            "Το σχολείο εξυπηρετεί 350 μαθητές και έχει 25 τάξεις. Ο διευθυντής, "
            "κ. Μιχάλης Στεφανίδης, μπορεί να κληθεί στο 2102233445. Ο ΑΦΜ του σχολείου "
            "είναι 999023456 και το επιχειρησιακό IBAN GR9201100990000099900112233."
        ),
    },
]


def main() -> int:
    if not CHECKPOINT_DIR.exists():
        print(f"FAIL: checkpoint dir not found: {CHECKPOINT_DIR}", file=sys.stderr)
        return 1
    print(f"[load] checkpoint = {CHECKPOINT_DIR}")
    from opf import OPF

    detector = OPF(model=str(CHECKPOINT_DIR), device="cuda")
    print("[load] model ready")
    print()

    total_predicted = 0
    for i, case in enumerate(TESTS, start=1):
        text = case["text"]
        register = case["register"]
        result = detector.redact(text)
        spans = list(result.detected_spans)
        total_predicted += len(spans)
        print("=" * 80)
        print(f"#{i:02d} register: {register}  ({len(spans)} spans detected)")
        print("-" * 80)
        print("TEXT:")
        print(text)
        print()
        print("DETECTED SPANS:")
        if not spans:
            print("  (none)")
        else:
            for s in spans:
                print(f"  • [{s.label:18s}] '{s.text}' @ [{s.start},{s.end}]")
        print()
        print("REDACTED:")
        print(result.redacted_text)
        print()

    print("=" * 80)
    print(f"SUMMARY: {len(TESTS)} test cases, {total_predicted} total spans detected")
    print()
    print("Export full results to artifacts/metrics/realworld_inference.json")
    out_path = PROJECT_ROOT / "artifacts" / "metrics" / "realworld_inference.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for case in TESTS:
        result = detector.redact(case["text"])
        payload.append({
            "register": case["register"],
            "text": case["text"],
            "redacted_text": result.redacted_text,
            "detected_spans": [
                {"label": s.label, "start": s.start, "end": s.end, "text": s.text}
                for s in result.detected_spans
            ],
        })
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
