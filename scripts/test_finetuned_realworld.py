"""Real-world inference test for the v1 fine-tuned Greek Privacy Filter.

Constructs realistic Greek-language test passages combining authentic
Greek prose patterns (legal text style, business correspondence, SMS,
medical chart, banking notification, etc.) with manually-crafted
synthetic PII spans. No real personal data is processed: every PII
value is fictional but follows the canonical Greek formats (AFM
9-digit, AMKA 11-digit, ADT 1-2 letters + 6 digits, IBAN GR + 25
digits, Greek mobile 69x prefix).

The script:

1. Loads a fine-tuned OPF checkpoint (path either from --checkpoint,
   the OPF_CHECKPOINT_DIR environment variable, or the v1 default
   under data/processed/aws-ft-20260426T135853Z/model/).
2. Runs ``OPF.redact`` on every test passage.
3. Compares predicted spans against hand-graded expected spans
   (label + value match; offset-position is ignored to keep the test
   robust against insignificant tokenisation drift).
4. Prints predicted vs expected side by side for every case.
5. Reports overall precision / recall / F1 plus the redacted text.
6. Writes a per-case JSON report to
   artifacts/metrics/realworld_inference.json.

Usage:

    python scripts/test_finetuned_realworld.py \
        --checkpoint data/processed/aws-ft-20260426T135853Z/model \
        --device cuda

Run without arguments to use the default v1 checkpoint path. Set
OPF_CHECKPOINT_DIR for a session-wide override.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "aws-ft-20260426T135853Z" / "model"
)


# Each entry: register, text, expected = list of {label, text} dicts.
# Expected spans encode the canonically-correct PII detection: span
# value only (never including a label prefix such as "ΑΦΜ ", "ΑΜΚΑ ",
# "Τηλ. " or trailing punctuation), and the most specific class for
# each value. v1's known weaknesses (AFM/ADT boundary creep on
# prefix-labelled IDs, phone-vs-account confusion on Greek mobile
# numbers in dense medical contexts, AMKA recall miss when the AMKA
# encodes the same date as a written birthdate) will surface as
# precision / recall losses against this gold standard.
TESTS = [
    {
        "register": "business email",
        "text": (
            "Καλημέρα κ. Παπαδόπουλε,\n\n"
            "Επιβεβαιώνουμε τη συνάντηση την Παρασκευή 30 Μαΐου 2025 στο γραφείο μας. "
            "Παρακαλώ επικοινωνήστε με τη γραμματεία μας στο 2103456789 ή στο "
            "info@law-firm-athens.gr για οποιαδήποτε αλλαγή."
        ),
        "expected": [
            {"label": "private_person", "text": "Παπαδόπουλε"},
            {"label": "private_date", "text": "30 Μαΐου 2025"},
            {"label": "private_phone", "text": "2103456789"},
            {"label": "private_email", "text": "info@law-firm-athens.gr"},
        ],
    },
    {
        "register": "SMS",
        "text": (
            "Γεια σου Μαρία! Ο γιατρός θέλει το ΑΜΚΑ σου 15076512345 και τον ΑΦΜ "
            "078123456 για τη συνταγή. Πες του και τη ΑΔΤ ΑΖ123456 πριν τη Δευτέρα."
        ),
        "expected": [
            {"label": "private_person", "text": "Μαρία"},
            {"label": "amka", "text": "15076512345"},
            {"label": "afm", "text": "078123456"},
            {"label": "adt", "text": "ΑΖ123456"},
        ],
    },
    {
        "register": "banking notification",
        "text": (
            "Αγαπητέ πελάτη, η μεταφορά 1.250,00€ προς τον λογαριασμό 014/220123456 "
            "(IBAN GR1601100140000001402201234) ολοκληρώθηκε την 15/06/2025. "
            "Ο νέος κωδικός μίας χρήσης είναι TX9-AB7-PQ42 και ισχύει για 5 λεπτά."
        ),
        "expected": [
            {"label": "account_number", "text": "014/220123456"},
            {"label": "iban_gr", "text": "GR1601100140000001402201234"},
            {"label": "private_date", "text": "15/06/2025"},
            {"label": "secret", "text": "TX9-AB7-PQ42"},
        ],
    },
    {
        "register": "medical chart",
        "text": (
            "Ασθενής: Γεώργιος Δημητρίου, ΑΜΚΑ 22018054321. Ημερομηνία γέννησης: 22/01/1980. "
            "Διεύθυνση: Αγίου Κωνσταντίνου 14, Πειραιάς. Τηλ. επικοινωνίας: 6981234567. "
            "Παραπεμπτικός ιατρός: dr.papadimitriou@iatreio.gr."
        ),
        "expected": [
            {"label": "private_person", "text": "Γεώργιος Δημητρίου"},
            {"label": "amka", "text": "22018054321"},
            {"label": "private_date", "text": "22/01/1980"},
            {"label": "private_address", "text": "Αγίου Κωνσταντίνου 14, Πειραιάς"},
            {"label": "private_phone", "text": "6981234567"},
            {"label": "private_email", "text": "dr.papadimitriou@iatreio.gr"},
        ],
    },
    {
        "register": "HR letter",
        "text": (
            "Με την παρούσα βεβαιώνουμε ότι ο κ. Νίκος Αντωνίου εργάζεται στην εταιρεία μας "
            "από 01/03/2018. Ο ΑΦΜ του είναι 134567890 και ο κωδικός τραπεζικού λογαριασμού "
            "που χρησιμοποιείται για μισθοδοσία είναι 175/487654321."
        ),
        "expected": [
            {"label": "private_person", "text": "Νίκος Αντωνίου"},
            {"label": "private_date", "text": "01/03/2018"},
            {"label": "afm", "text": "134567890"},
            {"label": "account_number", "text": "175/487654321"},
        ],
    },
    {
        "register": "support ticket",
        "text": (
            "Ticket #4421: Ο χρήστης δεν μπορεί να συνδεθεί. Email: kostas.giannidis@example.gr, "
            "URL προφίλ: https://platform.example.gr/users/12944. Παρακαλώ ελέγξτε το token "
            "σύνδεσης sk-LIVE-9a2bf7ed4c3e και ενημερώστε εάν χρειάζεται reset."
        ),
        "expected": [
            {"label": "private_email", "text": "kostas.giannidis@example.gr"},
            {"label": "private_url", "text": "https://platform.example.gr/users/12944"},
            {"label": "secret", "text": "sk-LIVE-9a2bf7ed4c3e"},
        ],
    },
    {
        "register": "government form",
        "text": (
            "Όνομα: Ελένη Παπανικολάου. Πατρώνυμο: Ιωάννης. Α.Δ.Τ.: ΑΗ987654. "
            "Διεύθυνση κατοικίας: Πατησίων 88, Αθήνα 10434. Τηλέφωνο: 2106789012. "
            "Ηλεκτρονικό ταχυδρομείο: e.papanikolaou@dimosio.gr."
        ),
        "expected": [
            {"label": "private_person", "text": "Ελένη Παπανικολάου"},
            {"label": "private_person", "text": "Ιωάννης"},
            {"label": "adt", "text": "ΑΗ987654"},
            {"label": "private_address", "text": "Πατησίων 88, Αθήνα 10434"},
            {"label": "private_phone", "text": "2106789012"},
            {"label": "private_email", "text": "e.papanikolaou@dimosio.gr"},
        ],
    },
    {
        "register": "carrier-only (no PII)",
        "text": (
            "Η Ελληνική Δημοκρατία αποτελεί κράτος δικαίου με κοινοβουλευτική δημοκρατία. "
            "Η οικονομία της βασίζεται στις υπηρεσίες, στον τουρισμό και στη γεωργία."
        ),
        "expected": [],
    },
    {
        "register": "mixed Greek/Latin contact",
        "text": (
            "Επικοινωνήστε στο τηλέφωνο 6987654321 ή στείλτε email στο νικος@παράδειγμα.gr "
            "για τη συνέντευξη της 03/07/2025. Η εταιρεία ΧΥΖ Α.Ε. βρίσκεται στη Λεωφόρο "
            "Αλεξάνδρας 105."
        ),
        "expected": [
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_email", "text": "νικος@παράδειγμα.gr"},
            {"label": "private_date", "text": "03/07/2025"},
            {"label": "private_address", "text": "Λεωφόρο Αλεξάνδρας 105"},
        ],
    },
    {
        "register": "tricky numerics (hard negatives + real PII)",
        "text": (
            "Το σχολείο εξυπηρετεί 350 μαθητές και έχει 25 τάξεις. Ο διευθυντής, "
            "κ. Μιχάλης Στεφανίδης, μπορεί να κληθεί στο 2102233445. Ο ΑΦΜ του σχολείου "
            "είναι 999023456 και το επιχειρησιακό IBAN GR9201100990000099900112233."
        ),
        "expected": [
            {"label": "private_person", "text": "Μιχάλης Στεφανίδης"},
            {"label": "private_phone", "text": "2102233445"},
            {"label": "afm", "text": "999023456"},
            {"label": "iban_gr", "text": "GR9201100990000099900112233"},
        ],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--checkpoint",
        default=os.environ.get("OPF_CHECKPOINT_DIR", str(DEFAULT_CHECKPOINT_DIR)),
        help=(
            "Directory containing the fine-tuned OPF checkpoint "
            "(model.safetensors + config.json + label_space.json + "
            "dtypes.json + viterbi_calibration.json). Falls back to "
            "$OPF_CHECKPOINT_DIR or the v1 default path under "
            "data/processed/aws-ft-20260426T135853Z/model/."
        ),
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("OPF_DEVICE", "cuda"),
        choices=["cuda", "cpu"],
        help="Inference device. Defaults to cuda; falls back via $OPF_DEVICE.",
    )
    parser.add_argument(
        "--metrics-out",
        default=str(PROJECT_ROOT / "artifacts" / "metrics" / "realworld_inference.json"),
        help="Path to write the per-case JSON report.",
    )
    return parser.parse_args()


def score_case(
    predicted: list[dict[str, str]],
    expected: list[dict[str, str]],
) -> tuple[int, int, int]:
    """Return (true_positives, predicted_count, expected_count) for a case.

    Match key: (label, text). Order does not matter. A predicted span
    counts as a true positive if any expected span has the same (label,
    text) tuple, and vice versa. Multiplicities are respected: if
    expected has the same span twice, a single predicted match scores
    one TP, not two.
    """
    expected_keys = [(e["label"], e["text"]) for e in expected]
    predicted_keys = [(p["label"], p["text"]) for p in predicted]
    remaining = list(expected_keys)
    tp = 0
    for key in predicted_keys:
        if key in remaining:
            remaining.remove(key)
            tp += 1
    return tp, len(predicted_keys), len(expected_keys)


def f1(tp: int, predicted_count: int, expected_count: int) -> tuple[float, float, float]:
    precision = tp / predicted_count if predicted_count else 0.0
    recall = tp / expected_count if expected_count else 0.0
    if precision + recall == 0.0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def main() -> int:
    args = parse_args()
    checkpoint_dir = Path(args.checkpoint).expanduser().resolve()
    if not checkpoint_dir.exists():
        print(
            f"FAIL: checkpoint dir not found: {checkpoint_dir}\n"
            f"      pass --checkpoint <path> or set $OPF_CHECKPOINT_DIR.",
            file=sys.stderr,
        )
        return 1
    print(f"[load] checkpoint = {checkpoint_dir}")
    print(f"[load] device     = {args.device}")
    from opf import OPF  # type: ignore[import-not-found]

    detector = OPF(model=str(checkpoint_dir), device=args.device)
    print("[load] model ready")
    print()

    payload: list[dict] = []
    total_tp = 0
    total_predicted = 0
    total_expected = 0
    for i, case in enumerate(TESTS, start=1):
        text = case["text"]
        register = case["register"]
        expected = case["expected"]
        result = detector.redact(text)
        spans = list(result.detected_spans)
        predicted = [
            {"label": s.label, "start": s.start, "end": s.end, "text": s.text}
            for s in spans
        ]
        case_tp, case_predicted, case_expected = score_case(predicted, expected)
        case_p, case_r, case_f1 = f1(case_tp, case_predicted, case_expected)
        total_tp += case_tp
        total_predicted += case_predicted
        total_expected += case_expected

        print("=" * 80)
        print(
            f"#{i:02d} register: {register}  "
            f"(predicted {case_predicted} / expected {case_expected} / "
            f"matched {case_tp})"
        )
        print(
            f"    case P={case_p:.3f} R={case_r:.3f} F1={case_f1:.3f}"
        )
        print("-" * 80)
        print("TEXT:")
        print(text)
        print()
        print("EXPECTED SPANS:")
        if not expected:
            print("  (none — hard-negative case)")
        for e in expected:
            print(f"  • [{e['label']:18s}] '{e['text']}'")
        print()
        print("PREDICTED SPANS:")
        if not predicted:
            print("  (none)")
        for p in predicted:
            marker = (
                "  ✓"
                if (p["label"], p["text"]) in [(e["label"], e["text"]) for e in expected]
                else "  ✗"
            )
            print(f"{marker} [{p['label']:18s}] '{p['text']}' @ [{p['start']},{p['end']}]")
        print()
        print("REDACTED:")
        print(result.redacted_text)
        print()

        payload.append({
            "register": register,
            "text": text,
            "redacted_text": result.redacted_text,
            "expected_spans": expected,
            "detected_spans": predicted,
            "case_metrics": {
                "true_positives": case_tp,
                "predicted_count": case_predicted,
                "expected_count": case_expected,
                "precision": round(case_p, 4),
                "recall": round(case_r, 4),
                "f1": round(case_f1, 4),
            },
        })

    overall_p, overall_r, overall_f1 = f1(total_tp, total_predicted, total_expected)
    print("=" * 80)
    print(
        f"OVERALL: {len(TESTS)} cases, "
        f"predicted={total_predicted}, expected={total_expected}, "
        f"matched={total_tp}"
    )
    print(
        f"OVERALL: precision={overall_p:.4f}  recall={overall_r:.4f}  "
        f"F1={overall_f1:.4f}"
    )
    print()

    metrics_path = Path(args.metrics_out)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(
            {
                "checkpoint": str(checkpoint_dir),
                "device": args.device,
                "overall": {
                    "predicted_count": total_predicted,
                    "expected_count": total_expected,
                    "true_positives": total_tp,
                    "precision": round(overall_p, 4),
                    "recall": round(overall_r, 4),
                    "f1": round(overall_f1, 4),
                },
                "cases": payload,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"  wrote {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
