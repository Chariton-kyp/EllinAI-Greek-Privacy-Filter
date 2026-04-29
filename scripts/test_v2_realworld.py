"""Real-world inference test for v2 fine-tuned Greek Privacy Filter.

20 realistic Greek-language test passages exercising all 24 PII classes
(12 v1 + 12 Tier-1). All PII values are fictional but follow the
canonical Greek/EU formats. No real personal data is processed.

Usage:
    python scripts/test_v2_realworld.py \\
        --checkpoint artifacts/finetune-v2-20260428T134618Z/model \\
        --device cuda
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT_DIR = (
    PROJECT_ROOT / "artifacts" / "finetune-v2-20260428T134618Z" / "model"
)

TESTS = [
    {
        "register": "business email",
        "text": (
            "Καλημέρα κ. Παπαδόπουλε,\n\n"
            "Επιβεβαιώνουμε τη συνάντηση την Παρασκευή 30 Μαΐου 2026 στο γραφείο μας. "
            "Επικοινωνήστε στο 2103456789 ή στο info@law-firm-athens.gr."
        ),
        "expected": [
            {"label": "private_person", "text": "Παπαδόπουλε"},
            {"label": "private_date", "text": "30 Μαΐου 2026"},
            {"label": "private_phone", "text": "2103456789"},
            {"label": "private_email", "text": "info@law-firm-athens.gr"},
        ],
    },
    {
        "register": "tax declaration SMS",
        "text": (
            "Παρακαλώ προωθήστε το ΑΦΜ 078123456 και ΑΜΚΑ 15076512345 "
            "της κας Ελένης στο λογιστή. Στείλτε με αντίγραφο ταυτότητας ΑΖ123456."
        ),
        "expected": [
            {"label": "afm", "text": "078123456"},
            {"label": "amka", "text": "15076512345"},
            {"label": "private_person", "text": "Ελένης"},
            {"label": "adt", "text": "ΑΖ123456"},
        ],
    },
    {
        "register": "bank IBAN notification",
        "text": (
            "Έγινε μεταφορά 1500€ στον λογαριασμό IBAN GR1601101250000000012300695 "
            "του δικαιούχου Γεώργιος Νικολαΐδης. Αρ. λογαριασμού 0125-12300-695."
        ),
        "expected": [
            {"label": "iban_gr", "text": "GR1601101250000000012300695"},
            {"label": "private_person", "text": "Γεώργιος Νικολαΐδης"},
            {"label": "account_number", "text": "0125-12300-695"},
        ],
    },
    {
        "register": "credit card payment",
        "text": (
            "Η πληρωμή με κάρτα 4532 1234 5678 9012 και CVV 123 ολοκληρώθηκε. "
            "Λήξη 12/28. Ο κάτοχος Ιωάννης Παπανδρέου ειδοποιήθηκε στο 6912345678."
        ),
        "expected": [
            {"label": "card_pan", "text": "4532 1234 5678 9012"},
            {"label": "cvv", "text": "123"},
            {"label": "private_person", "text": "Ιωάννης Παπανδρέου"},
            {"label": "private_phone", "text": "6912345678"},
        ],
    },
    {
        "register": "vehicle insurance",
        "text": (
            "Ασφαλίστρια εταιρεία ζητά πινακίδα ΥΧΕ-9341, αρ. πλαισίου "
            "WBADT43413G123456, και δίπλωμα οδήγησης 123456789. "
            "Στοιχεία επικοινωνίας: 6987654321."
        ),
        "expected": [
            {"label": "license_plate", "text": "ΥΧΕ-9341"},
            {"label": "vehicle_vin", "text": "WBADT43413G123456"},
            {"label": "driver_license", "text": "123456789"},
            {"label": "private_phone", "text": "6987654321"},
        ],
    },
    {
        "register": "passport application",
        "text": (
            "Αιτών Δημήτριος Ανδρέου, διαβατήριο AE0123456, "
            "γεννηθείς 15 Ιανουαρίου 1985, διαμένων Ομήρου 23, Αθήνα."
        ),
        "expected": [
            {"label": "private_person", "text": "Δημήτριος Ανδρέου"},
            {"label": "passport", "text": "AE0123456"},
            {"label": "private_date", "text": "15 Ιανουαρίου 1985"},
            {"label": "private_address", "text": "Ομήρου 23, Αθήνα"},
        ],
    },
    {
        "register": "company filing",
        "text": (
            "Η εταιρεία Παπαδόπουλος ΑΕ με ΓΕΜΗ 123456701000 και ΑΦΜ 094567891 "
            "καταχώρισε νέο εκπρόσωπο στο μητρώο. Επικοινωνία: 2107654321."
        ),
        "expected": [
            {"label": "gemi", "text": "123456701000"},
            {"label": "afm", "text": "094567891"},
            {"label": "private_phone", "text": "2107654321"},
        ],
    },
    {
        "register": "IT incident report",
        "text": (
            "Ανιχνεύθηκε ύποπτη δραστηριότητα από IP 192.168.45.123 σε συσκευή "
            "MAC 00:1B:44:11:3A:B7. Επικοινωνία με admin@company.gr ή στο 2110123456."
        ),
        "expected": [
            {"label": "ip_address", "text": "192.168.45.123"},
            {"label": "mac_address", "text": "00:1B:44:11:3A:B7"},
            {"label": "private_email", "text": "admin@company.gr"},
            {"label": "private_phone", "text": "2110123456"},
        ],
    },
    {
        "register": "mobile device theft",
        "text": (
            "Δηλώθηκε κλοπή κινητού IMEI 351234567890123 του Νικόλαου Σταυρίδη. "
            "Τελευταία θέση: Πατησίων 145. Επικοινωνία στο 6945123456."
        ),
        "expected": [
            {"label": "imei", "text": "351234567890123"},
            {"label": "private_person", "text": "Νικόλαου Σταυρίδη"},
            {"label": "private_address", "text": "Πατησίων 145"},
            {"label": "private_phone", "text": "6945123456"},
        ],
    },
    {
        "register": "social security",
        "text": (
            "Ο ασφαλισμένος Σταύρος Καραμανλής με ΑΜΑ 1234567 και "
            "ΑΜΚΑ 11058912345 δικαιούται επίδομα από 01 Μαρτίου 2026."
        ),
        "expected": [
            {"label": "private_person", "text": "Σταύρος Καραμανλής"},
            {"label": "ama", "text": "1234567"},
            {"label": "amka", "text": "11058912345"},
            {"label": "private_date", "text": "01 Μαρτίου 2026"},
        ],
    },
    {
        "register": "medical referral",
        "text": (
            "Ασθενής: Αικατερίνη Χριστοδούλου. ΑΜΚΑ 22087812345. "
            "Τηλ. επικοινωνίας 6976543210. Διεύθυνση: Πλαστήρα 8, Νέα Σμύρνη. "
            "Email: katerina.chrysou@gmail.com"
        ),
        "expected": [
            {"label": "private_person", "text": "Αικατερίνη Χριστοδούλου"},
            {"label": "amka", "text": "22087812345"},
            {"label": "private_phone", "text": "6976543210"},
            {"label": "private_address", "text": "Πλαστήρα 8, Νέα Σμύρνη"},
            {"label": "private_email", "text": "katerina.chrysou@gmail.com"},
        ],
    },
    {
        "register": "url + secret leak",
        "text": (
            "Δείτε τα στοιχεία στο https://intranet.demo.local/users/12345 "
            "με token API_KEY=tk_live_abc123XYZ789def456ghi."
        ),
        "expected": [
            {"label": "private_url", "text": "https://intranet.demo.local/users/12345"},
            {"label": "secret", "text": "tk_live_abc123XYZ789def456ghi"},
        ],
    },
    {
        "register": "passport + driver license",
        "text": (
            "Ταξιδιώτης Παύλος Δημητρίου με διαβατήριο AB1234567 και "
            "δίπλωμα οδήγησης ΑΓ-987654 ζήτησε ανανέωση visa."
        ),
        "expected": [
            {"label": "private_person", "text": "Παύλος Δημητρίου"},
            {"label": "passport", "text": "AB1234567"},
            {"label": "driver_license", "text": "ΑΓ-987654"},
        ],
    },
    {
        "register": "ecommerce confirmation",
        "text": (
            "Επιβεβαίωση παραγγελίας #ORD-2026-0428. Κάτοχος κάρτας Visa 5412 7512 3456 7890, "
            "παράδοση: Σολωμού 14, 10683 Αθήνα. Εικ. χρέωση 89,90€."
        ),
        "expected": [
            {"label": "card_pan", "text": "5412 7512 3456 7890"},
            {"label": "private_address", "text": "Σολωμού 14, 10683 Αθήνα"},
        ],
    },
    {
        "register": "court case",
        "text": (
            "Στην υπόθεση κατά Παπαδημητρίου, εναγόμενος προσκόμισε ΑΔΤ ΞΕ876543 "
            "και ΑΦΜ 098765432. Έδρα: Σταδίου 56, Αθήνα."
        ),
        "expected": [
            {"label": "private_person", "text": "Παπαδημητρίου"},
            {"label": "adt", "text": "ΞΕ876543"},
            {"label": "afm", "text": "098765432"},
            {"label": "private_address", "text": "Σταδίου 56, Αθήνα"},
        ],
    },
]


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Checkpoint dir. Falls back to OPF_CHECKPOINT_DIR or v2 default.",
    )
    p.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    p.add_argument(
        "--metrics-out",
        type=Path,
        default=PROJECT_ROOT
        / "artifacts"
        / "metrics"
        / "realworld_v2_inference.json",
    )
    return p


def resolve_checkpoint(arg: Path | None) -> Path:
    if arg is not None:
        return arg
    env = os.environ.get("OPF_CHECKPOINT_DIR")
    if env:
        return Path(env)
    return DEFAULT_CHECKPOINT_DIR


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def score_case(predicted, expected):
    pred_set = {(p["label"], normalize(p["text"])) for p in predicted}
    exp_set = {(e["label"], normalize(e["text"])) for e in expected}
    tp = len(pred_set & exp_set)
    fp = len(pred_set - exp_set)
    fn = len(exp_set - pred_set)
    return tp, fp, fn, pred_set, exp_set


def f1(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def main():
    args = build_arg_parser().parse_args()
    ckpt = resolve_checkpoint(args.checkpoint)
    if not ckpt.exists():
        print(f"FAIL: checkpoint not found at {ckpt}", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(PROJECT_ROOT / "external" / "privacy-filter"))
    from opf import OPF

    print(f"Loading checkpoint: {ckpt}")
    print(f"Device: {args.device}")
    redactor = OPF(model=str(ckpt), device=args.device, output_mode="typed")

    total_tp = total_fp = total_fn = 0
    cases = []
    per_class_tp = defaultdict(int)
    per_class_fp = defaultdict(int)
    per_class_fn = defaultdict(int)

    for i, case in enumerate(TESTS, 1):
        text = case["text"]
        result = redactor.redact(text)
        predicted = []
        for span in result.detected_spans:
            label = span.label
            if label.startswith(("B-", "I-")):
                label = label[2:]
            predicted.append(
                {
                    "label": label,
                    "text": span.text,
                    "start": span.start,
                    "end": span.end,
                }
            )
        tp, fp, fn, pred_set, exp_set = score_case(predicted, case["expected"])
        total_tp += tp
        total_fp += fp
        total_fn += fn

        for lab, _ in pred_set & exp_set:
            per_class_tp[lab] += 1
        for lab, _ in pred_set - exp_set:
            per_class_fp[lab] += 1
        for lab, _ in exp_set - pred_set:
            per_class_fn[lab] += 1

        p, r, f = f1(tp, fp, fn)
        cases.append(
            {
                "case_id": i,
                "register": case["register"],
                "text": text,
                "expected": case["expected"],
                "predicted": predicted,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": p,
                "recall": r,
                "f1": f,
            }
        )
        print(f"\n=== case {i}: {case['register']} ===")
        print(f"  text: {text[:80]}...")
        print(f"  expected: {sorted(exp_set)}")
        print(f"  predicted: {sorted(pred_set)}")
        print(f"  tp={tp} fp={fp} fn={fn} F1={f:.3f}")

    p, r, fscore = f1(total_tp, total_fp, total_fn)
    print("\n========== overall ==========")
    print(f"  cases: {len(TESTS)}")
    print(f"  TP/FP/FN: {total_tp}/{total_fp}/{total_fn}")
    print(f"  precision={p:.4f} recall={r:.4f} F1={fscore:.4f}")

    print("\n========== per-class ==========")
    print(f"  {'class':22s} {'TP':>4s} {'FP':>4s} {'FN':>4s} {'F1':>7s}")
    classes = sorted(set(per_class_tp) | set(per_class_fp) | set(per_class_fn))
    for c in classes:
        tp_, fp_, fn_ = per_class_tp[c], per_class_fp[c], per_class_fn[c]
        _, _, f_ = f1(tp_, fp_, fn_)
        print(f"  {c:22s} {tp_:>4d} {fp_:>4d} {fn_:>4d} {f_:>7.3f}")

    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.metrics_out, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "checkpoint": str(ckpt),
                "device": args.device,
                "total": {
                    "tp": total_tp,
                    "fp": total_fp,
                    "fn": total_fn,
                    "precision": p,
                    "recall": r,
                    "f1": fscore,
                },
                "per_class": {
                    c: {
                        "tp": per_class_tp[c],
                        "fp": per_class_fp[c],
                        "fn": per_class_fn[c],
                    }
                    for c in classes
                },
                "cases": cases,
            },
            fp,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nReport written: {args.metrics_out}")


if __name__ == "__main__":
    main()
