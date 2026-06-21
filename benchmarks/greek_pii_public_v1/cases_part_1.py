"""Greek PII Public Benchmark v1 — Part 1 (cases 1-25).

Tax/Government (1-10), Medical (11-20), Banking start (21-25).

All values synthetic. License: CC-BY-4.0.
"""
from __future__ import annotations

CASES = [
    # ============== TAX / GOVERNMENT (1-10) ==============
    {
        "id": 1,
        "register": "tax_demand_letter",
        "text": (
            "ΑΑΔΕ — ΔΟΥ Α' Πειραιά\n\n"
            "Προς: κ. Σταύρο Λεοντιάδη\n"
            "Διεύθυνση: Ομήρου 14, 18537 Πειραιάς\n"
            "ΑΦΜ: 187654932 | ΑΜΚΑ: 12058923456\n"
            "Email: stavros.leontiadis@example.gr | Τηλ: 2104567823\n\n"
            "Σας ενημερώνουμε ότι εκκρεμεί φόρος εισοδήματος 1.245€ "
            "για το έτος 2025. Πληρωμή έως 30/06/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Σταύρο Λεοντιάδη"},
            {"label": "private_address", "text": "Ομήρου 14, 18537 Πειραιάς"},
            {"label": "afm", "text": "187654932"},
            {"label": "amka", "text": "12058923456"},
            {"label": "private_email", "text": "stavros.leontiadis@example.gr"},
            {"label": "private_phone", "text": "2104567823"},
            {"label": "private_date", "text": "30/06/2026"},
        ],
    },
    {
        "id": 2,
        "register": "efka_pension_notice",
        "text": (
            "ΕΦΚΑ — Ηλεκτρονική Υπηρεσία\n\n"
            "Αγαπητή κα Παππά,\n"
            "Η αίτηση συνταξιοδότησης (αρ. πρωτ. 2026/45123) εγκρίθηκε. "
            "Στοιχεία δικαιούχου: Άννα Παππά, ΑΜΚΑ 23117045123, "
            "ΑΜΑ ΙΚΑ: 7845612, ΑΔΤ: ΑΕ-589123. "
            "Πρώτη καταβολή: 15/07/2026 σε IBAN GR16 0140 6500 6500 0011 4587 998."
        ),
        "spans": [
            {"label": "private_person", "text": "Άννα Παππά"},
            {"label": "amka", "text": "23117045123"},
            {"label": "ama", "text": "7845612"},
            {"label": "adt", "text": "ΑΕ-589123"},
            {"label": "private_date", "text": "15/07/2026"},
            {"label": "iban_gr", "text": "GR16 0140 6500 6500 0011 4587 998"},
        ],
    },
    {
        "id": 3,
        "register": "tax_e1_form",
        "text": (
            "ΕΝΤΥΠΟ Ε1 — Φορολογικό Έτος 2025\n"
            "Ονοματεπώνυμο: ΓΕΩΡΓΙΟΣ ΑΘΑΝΑΣΟΠΟΥΛΟΣ\n"
            "ΑΦΜ: 045672891\n"
            "Διεύθυνση κατοικίας: Πατησίων 178, 11251 Αθήνα\n"
            "Επάγγελμα: Λογιστής\n"
            "Τηλέφωνο: 6932451890\n"
            "ΓΕΜΗ (ατομικής επιχείρησης): 165432100000\n\n"
            "Συνολικό εισόδημα: 38.450,00€\n"
            "Φόρος: 7.690,00€"
        ),
        "spans": [
            {"label": "private_person", "text": "ΓΕΩΡΓΙΟΣ ΑΘΑΝΑΣΟΠΟΥΛΟΣ"},
            {"label": "afm", "text": "045672891"},
            {"label": "private_address", "text": "Πατησίων 178, 11251 Αθήνα"},
            {"label": "private_phone", "text": "6932451890"},
            {"label": "gemi", "text": "165432100000"},
        ],
    },
    {
        "id": 4,
        "register": "doy_audit_summons",
        "text": (
            "ΔΟΥ Νέας Ιωνίας\nΑριθμ. Πρωτ. 8723/2026\n\n"
            "Καλείστε στις 12 Μαΐου 2026 για έλεγχο φορολογικών στοιχείων.\n"
            "Στοιχεία: ΕΛΕΝΗ ΡΟΔΙΤΗ, ΑΦΜ 234567812, ΑΔΤ ΑΖ-345678.\n"
            "ΠΑΠ: 451237890Q12.\n"
            "Παρακαλούμε προσκομίστε αντίγραφο διαβατηρίου ΑΜ4567823.\n"
            "Email επικοινωνίας: doy.nion@aade.gr"
        ),
        "spans": [
            {"label": "private_date", "text": "12 Μαΐου 2026"},
            {"label": "private_person", "text": "ΕΛΕΝΗ ΡΟΔΙΤΗ"},
            {"label": "afm", "text": "234567812"},
            {"label": "adt", "text": "ΑΖ-345678"},
            {"label": "pcn", "text": "451237890Q12"},
            {"label": "passport", "text": "ΑΜ4567823"},
            {"label": "private_email", "text": "doy.nion@aade.gr"},
        ],
    },
    {
        "id": 5,
        "register": "gov_decree",
        "text": (
            "ΕΦΗΜΕΡΙΣ ΤΗΣ ΚΥΒΕΡΝΗΣΕΩΣ\nΦΕΚ Β' 2456 / 22-03-2026\n\n"
            "Απόφαση Υπουργείου Υγείας\n"
            "Διορίζεται ως αναπληρωτής διευθυντής ο κ. Νικόλαος Φραντζής "
            "του Δημητρίου, ΑΔΤ ΑΡ-892341, κάτοικος Λαρίσης 67, 41335 Λάρισα. "
            "Επικοινωνία: 2410678234. "
            "Έναρξη θητείας: 01/04/2026."
        ),
        "spans": [
            {"label": "private_date", "text": "22-03-2026"},
            {"label": "private_person", "text": "Νικόλαος Φραντζής"},
            {"label": "adt", "text": "ΑΡ-892341"},
            {"label": "private_address", "text": "Λαρίσης 67, 41335 Λάρισα"},
            {"label": "private_phone", "text": "2410678234"},
            {"label": "private_date", "text": "01/04/2026"},
        ],
    },
    {
        "id": 6,
        "register": "municipal_pcn_letter",
        "text": (
            "Δήμος Θεσσαλονίκης — Αίτηση Πιστοποιητικού\n\n"
            "Δημότης: Μαρία Σαμαρά\n"
            "ΠΑΠ: 567812340X45\n"
            "Διεύθυνση: Εθνικής Αντιστάσεως 12, 54622 Θεσσαλονίκη\n"
            "Τηλ: 2310456789\n"
            "Αριθμός αίτησης: 2026/MUN-456\n"
            "Ημερομηνία υποβολής: 18/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Μαρία Σαμαρά"},
            {"label": "pcn", "text": "567812340X45"},
            {"label": "private_address", "text": "Εθνικής Αντιστάσεως 12, 54622 Θεσσαλονίκη"},
            {"label": "private_phone", "text": "2310456789"},
            {"label": "private_date", "text": "18/04/2026"},
        ],
    },
    {
        "id": 7,
        "register": "tax_clearance_certificate",
        "text": (
            "Φορολογική Ενημερότητα\n"
            "Δικαιούχος: Ιωάννης Γκικόπουλος\n"
            "ΑΦΜ: 067834521\n"
            "ΠΑΠ: 824651320R37\n"
            "Διεύθυνση: 25ης Μαρτίου 8, 17671 Καλλιθέα\n"
            "Email: gikopoulos.i@example.com\n"
            "Ισχύει έως: 30/09/2026\n"
            "Εκδόθηκε στις: 15/03/2026 από aade.gr/eforia"
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννης Γκικόπουλος"},
            {"label": "afm", "text": "067834521"},
            {"label": "pcn", "text": "824651320R37"},
            {"label": "private_address", "text": "25ης Μαρτίου 8, 17671 Καλλιθέα"},
            {"label": "private_email", "text": "gikopoulos.i@example.com"},
            {"label": "private_date", "text": "30/09/2026"},
            {"label": "private_date", "text": "15/03/2026"},
            {"label": "private_url", "text": "aade.gr/eforia"},
        ],
    },
    {
        "id": 8,
        "register": "kep_application",
        "text": (
            "ΚΕΠ Πειραιά — Πιστοποιητικό Γέννησης\n"
            "Αιτών: Δημήτριος Παρασκευάς, γεν. 14/06/1985\n"
            "ΑΔΤ: ΞΗ-678123\n"
            "ΑΜΚΑ: 14068550012\n"
            "Διεύθυνση: Σωκράτους 45, 18536 Πειραιάς\n"
            "Κιν.: 6987654321 | Email: paraskevasd@example.gr"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτριος Παρασκευάς"},
            {"label": "private_date", "text": "14/06/1985"},
            {"label": "adt", "text": "ΞΗ-678123"},
            {"label": "amka", "text": "14068550012"},
            {"label": "private_address", "text": "Σωκράτους 45, 18536 Πειραιάς"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_email", "text": "paraskevasd@example.gr"},
        ],
    },
    {
        "id": 9,
        "register": "tax_office_email",
        "text": (
            "From: doy.athens@aade.gr\n"
            "To: kostas.papadakis@firm.gr\n"
            "Θέμα: ΦΠΑ Α' τριμήνου 2026\n\n"
            "Κύριε Παπαδάκη, η εταιρεία σας με ΓΕΜΗ 089451200000 και "
            "ΑΦΜ 094782315 οφείλει να υποβάλει την περιοδική δήλωση Φ2 "
            "έως την 25 Φεβρουαρίου 2026. Πληροφορίες: aade.gr/vat-quarterly"
        ),
        "spans": [
            {"label": "private_email", "text": "doy.athens@aade.gr"},
            {"label": "private_email", "text": "kostas.papadakis@firm.gr"},
            {"label": "private_person", "text": "Παπαδάκη"},
            {"label": "gemi", "text": "089451200000"},
            {"label": "afm", "text": "094782315"},
            {"label": "private_date", "text": "25 Φεβρουαρίου 2026"},
            {"label": "private_url", "text": "aade.gr/vat-quarterly"},
        ],
    },
    {
        "id": 10,
        "register": "passport_renewal",
        "text": (
            "Διεύθυνση Διαβατηρίων Αθηνών\n"
            "Αίτηση ανανέωσης διαβατηρίου\n"
            "Στοιχεία: Στέφανος Αναγνωστόπουλος\n"
            "Παλαιό διαβατήριο: ΑΕ7234567\n"
            "ΑΔΤ: ΑΝ-456123\n"
            "Ημερομηνία γέννησης: 03/11/1978\n"
            "Διεύθυνση: Φιλελλήνων 22, 10557 Αθήνα\n"
            "Τηλ: 2103412567 | Κιν: 6945123478"
        ),
        "spans": [
            {"label": "private_person", "text": "Στέφανος Αναγνωστόπουλος"},
            {"label": "passport", "text": "ΑΕ7234567"},
            {"label": "adt", "text": "ΑΝ-456123"},
            {"label": "private_date", "text": "03/11/1978"},
            {"label": "private_address", "text": "Φιλελλήνων 22, 10557 Αθήνα"},
            {"label": "private_phone", "text": "2103412567"},
            {"label": "private_phone", "text": "6945123478"},
        ],
    },
    # ============== MEDICAL / HEALTHCARE (11-20) ==============
    {
        "id": 11,
        "register": "medical_referral",
        "text": (
            "Νοσοκομείο Λαϊκό — Παραπεμπτικό\n"
            "Ασθενής: Ευαγγελία Καρβέλα\n"
            "ΑΜΚΑ: 28069145678 | Ημ.γέννησης: 28/06/1991\n"
            "Διεύθυνση: Σόλωνος 156, 10672 Αθήνα\n"
            "Τηλ.: 6976543210\n"
            "Διάγνωση: Διαβήτης Τύπου 2\n"
            "Συνταγογράφηση: Metformin 850mg\n"
            "Παραπέμπων: Δρ. Αντωνόπουλος, ΑΜΑ ασφαλισμένου: 5634127"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευαγγελία Καρβέλα"},
            {"label": "amka", "text": "28069145678"},
            {"label": "private_date", "text": "28/06/1991"},
            {"label": "private_address", "text": "Σόλωνος 156, 10672 Αθήνα"},
            {"label": "private_phone", "text": "6976543210"},
            {"label": "private_person", "text": "Αντωνόπουλος"},
            {"label": "ama", "text": "5634127"},
        ],
    },
    {
        "id": 12,
        "register": "prescription",
        "text": (
            "Συνταγή Φαρμάκων (ηλεκτρονική)\n"
            "Ασθενής: Παναγιώτης Δουκάκης, ΑΜΚΑ 17089034567\n"
            "Ιατρός: Δρ. Σοφία Καλομοίρη, ΑΜΑ 4523189\n"
            "Email ιατρού: kalomoiri.s@example.com\n"
            "Φαρμακείο: Ευαγγελιστρίας 14, 16562 Γλυφάδα\n"
            "Φάρμακα: Atorvastatin 20mg (90 δισκία)\n"
            "Ημερομηνία: 22/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Παναγιώτης Δουκάκης"},
            {"label": "amka", "text": "17089034567"},
            {"label": "private_person", "text": "Σοφία Καλομοίρη"},
            {"label": "ama", "text": "4523189"},
            {"label": "private_email", "text": "kalomoiri.s@example.com"},
            {"label": "private_address", "text": "Ευαγγελιστρίας 14, 16562 Γλυφάδα"},
            {"label": "private_date", "text": "22/04/2026"},
        ],
    },
    {
        "id": 13,
        "register": "medical_record",
        "text": (
            "ΝΟΣΟΚΟΜΕΙΟ ΕΥΑΓΓΕΛΙΣΜΟΣ — Ιατρικός Φάκελος\n\n"
            "Ονοματεπώνυμο: Σοφία Καρρά\n"
            "ΑΜΚΑ: 27098046789\n"
            "Ημ. Γέννησης: 27/09/1980\n"
            "Διεύθυνση: Φιλελλήνων 14, 17671 Καλλιθέα\n"
            "Τηλέφωνο: 2109876543\n"
            "Κινητό: 6909876543\n\n"
            "Διάγνωση: Υπέρταση\n"
            "Φάρμακα: Ramipril 5mg ημερησίως\n"
            "Επιβλέπων: Δρ. Καρρά Ευστάθιος, ΑΔΤ ΑΕ-345671"
        ),
        "spans": [
            {"label": "private_person", "text": "Σοφία Καρρά"},
            {"label": "amka", "text": "27098046789"},
            {"label": "private_date", "text": "27/09/1980"},
            {"label": "private_address", "text": "Φιλελλήνων 14, 17671 Καλλιθέα"},
            {"label": "private_phone", "text": "2109876543"},
            {"label": "private_phone", "text": "6909876543"},
            {"label": "private_person", "text": "Καρρά Ευστάθιος"},
            {"label": "adt", "text": "ΑΕ-345671"},
        ],
    },
    {
        "id": 14,
        "register": "lab_results",
        "text": (
            "Διαγνωστικό Κέντρο Βιοϊατρική\n"
            "Αποτελέσματα Εξετάσεων\n"
            "Ασθενής: Αλέξανδρος Παππάς\n"
            "ΑΜΚΑ: 19038512345 | Τηλ: 6987456321\n"
            "Email: alex.papas@example.gr\n"
            "Παραπέμπων ιατρός: Δρ. Δημητρίου, ΑΜΑ 6789123\n"
            "Ημερομηνία λήψης: 11/05/2026\n"
            "Ολική χοληστερόλη: 245 mg/dL"
        ),
        "spans": [
            {"label": "private_person", "text": "Αλέξανδρος Παππάς"},
            {"label": "amka", "text": "19038512345"},
            {"label": "private_phone", "text": "6987456321"},
            {"label": "private_email", "text": "alex.papas@example.gr"},
            {"label": "private_person", "text": "Δημητρίου"},
            {"label": "ama", "text": "6789123"},
            {"label": "private_date", "text": "11/05/2026"},
        ],
    },
    {
        "id": 15,
        "register": "hospital_admission",
        "text": (
            "Νοσοκομείο Γ. Γεννηματάς — Εισαγωγή Ασθενούς\n"
            "Ονοματεπώνυμο: Θεοδώρα Λεμπέση\n"
            "ΑΔΤ: ΑΞ-234567 | ΑΜΚΑ: 05078756123\n"
            "Διεύθυνση: Αλεξάνδρας 132, 11522 Αθήνα\n"
            "Τηλ. επικοινωνίας: 2106452389\n"
            "Πλησιέστερος συγγενής: Νίκος Λεμπέσης (κιν. 6932451768)\n"
            "Ασφαλιστικό ταμείο: ΕΦΚΑ\n"
            "Ημ. εισαγωγής: 28/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Θεοδώρα Λεμπέση"},
            {"label": "adt", "text": "ΑΞ-234567"},
            {"label": "amka", "text": "05078756123"},
            {"label": "private_address", "text": "Αλεξάνδρας 132, 11522 Αθήνα"},
            {"label": "private_phone", "text": "2106452389"},
            {"label": "private_person", "text": "Νίκος Λεμπέσης"},
            {"label": "private_phone", "text": "6932451768"},
            {"label": "private_date", "text": "28/04/2026"},
        ],
    },
    {
        "id": 16,
        "register": "vaccination_certificate",
        "text": (
            "Πιστοποιητικό Εμβολιασμού\n"
            "Όνομα: Κωνσταντίνος Σιδεράς\n"
            "ΑΜΚΑ: 30109056789\n"
            "Ημ.γέν: 30/10/1990 | ΑΔΤ ΑΗ-789123\n"
            "Εμβόλιο: COVID-19 (booster)\n"
            "Ημ.: 14/01/2026 | Φορέας: ΕΟΔΥ\n"
            "Επικοινωνία: eody.gov.gr/vax"
        ),
        "spans": [
            {"label": "private_person", "text": "Κωνσταντίνος Σιδεράς"},
            {"label": "amka", "text": "30109056789"},
            {"label": "private_date", "text": "30/10/1990"},
            {"label": "adt", "text": "ΑΗ-789123"},
            {"label": "private_date", "text": "14/01/2026"},
            {"label": "private_url", "text": "eody.gov.gr/vax"},
        ],
    },
    {
        "id": 17,
        "register": "doctor_chat_secret",
        "text": (
            "Δρ. Αθανασίου, καλημέρα. Παρακαλώ ανεβάστε τα νέα αποτελέσματα "
            "του ασθενούς Νικόλαου Παύλου (ΑΜΚΑ 21125634789) στο portal. "
            "API token: tk_live_4a7b2c9e8f1d6e5b3a2c\n"
            "Server IP: 192.168.1.45\n"
            "Email: athanasiou.dr@example.com"
        ),
        "spans": [
            {"label": "private_person", "text": "Αθανασίου"},
            {"label": "private_person", "text": "Νικόλαου Παύλου"},
            {"label": "amka", "text": "21125634789"},
            {"label": "secret", "text": "tk_live_4a7b2c9e8f1d6e5b3a2c"},
            {"label": "ip_address", "text": "192.168.1.45"},
            {"label": "private_email", "text": "athanasiou.dr@example.com"},
        ],
    },
    {
        "id": 18,
        "register": "telehealth_appointment",
        "text": (
            "Επιβεβαίωση Τηλεϊατρικής\n"
            "Ασθενής: Δέσποινα Μαυρομάτη\n"
            "ΑΜΚΑ: 08038423456\n"
            "Ραντεβού: 15/06/2026 11:30\n"
            "Σύνδεσμος: telehealth.platform.gr/room/x7g3f1\n"
            "Κωδικός σύνδεσης: med-2026-456789\n"
            "Τηλ. υποστήριξης: 2106789012"
        ),
        "spans": [
            {"label": "private_person", "text": "Δέσποινα Μαυρομάτη"},
            {"label": "amka", "text": "08038423456"},
            {"label": "private_date", "text": "15/06/2026"},
            {"label": "private_url", "text": "telehealth.platform.gr/room/x7g3f1"},
            {"label": "secret", "text": "med-2026-456789"},
            {"label": "private_phone", "text": "2106789012"},
        ],
    },
    {
        "id": 19,
        "register": "medical_insurance_claim",
        "text": (
            "Αίτηση Αποζημίωσης Ιδιωτικής Ασφάλισης\n"
            "Ασφαλισμένος: Ιωάννα Πετρούση\n"
            "ΑΜΚΑ: 11067845612 | ΑΦΜ: 098765432\n"
            "Αρ. συμβολαίου: HEALTH-2026-789456\n"
            "IBAN επιστροφής: GR91 0260 6920 0000 5000 0123 456\n"
            "Email: i.petrousi@example.gr | Κιν: 6945678901\n"
            "Ποσό: 1.450,00€ | Ημ.: 03/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννα Πετρούση"},
            {"label": "amka", "text": "11067845612"},
            {"label": "afm", "text": "098765432"},
            {"label": "iban_gr", "text": "GR91 0260 6920 0000 5000 0123 456"},
            {"label": "private_email", "text": "i.petrousi@example.gr"},
            {"label": "private_phone", "text": "6945678901"},
            {"label": "private_date", "text": "03/05/2026"},
        ],
    },
    {
        "id": 20,
        "register": "patient_chat_dense",
        "text": (
            "Γεια σας Δρ Καλόγερε, καλέσατε για τα αποτελέσματα; "
            "Ονομάζομαι Στέλιος Παπαϊωάννου (ΑΜΚΑ 04067445123). "
            "Με βρίσκετε στο 6987123456 ή στο stelios.p@example.com.\n"
            "ΑΔΤ ΑΛ-456789 για ταυτοποίηση. Ευχαριστώ!"
        ),
        "spans": [
            {"label": "private_person", "text": "Καλόγερε"},
            {"label": "private_person", "text": "Στέλιος Παπαϊωάννου"},
            {"label": "amka", "text": "04067445123"},
            {"label": "private_phone", "text": "6987123456"},
            {"label": "private_email", "text": "stelios.p@example.com"},
            {"label": "adt", "text": "ΑΛ-456789"},
        ],
    },
    # ============== BANKING (21-25, συνέχεια στο part 2) ==============
    {
        "id": 21,
        "register": "bank_transfer_notification",
        "text": (
            "Eurobank — Ειδοποίηση Συναλλαγής\n\n"
            "Αγαπητέ κ. Παπαδημητρίου,\n"
            "Η μεταφορά €2.450 από τον λογαριασμό IBAN GR91 0260 6920 0000 5000 0123 456 "
            "προς δικαιούχο Ιωάννη Καραμανλή ολοκληρώθηκε επιτυχώς στις 18/05/2026 14:35.\n"
            "Email: customer.service@eurobank.gr | Τηλ: 2109555555\n"
            "Αριθμός συναλλαγής: TRX-2026-518-7894521203"
        ),
        "spans": [
            {"label": "private_person", "text": "Παπαδημητρίου"},
            {"label": "iban_gr", "text": "GR91 0260 6920 0000 5000 0123 456"},
            {"label": "private_person", "text": "Ιωάννη Καραμανλή"},
            {"label": "private_date", "text": "18/05/2026"},
            {"label": "private_email", "text": "customer.service@eurobank.gr"},
            {"label": "private_phone", "text": "2109555555"},
            {"label": "account_number", "text": "TRX-2026-518-7894521203"},
        ],
    },
    {
        "id": 22,
        "register": "bank_card_alert",
        "text": (
            "Πειραιώς — Προειδοποίηση κάρτας\n"
            "Κάρτα: 4485 1267 3489 9012\n"
            "Δικαιούχος: Δημητρίου Στ.\n"
            "Συναλλαγή €890 στο Public.gr αρνήθηκε.\n"
            "Επικοινωνία: 2109876543 ή στο piraeusbank.gr/fraud-report\n"
            "Αν ήσασταν εσείς, καλέστε. Διαφορετικά μπλοκάρουμε."
        ),
        "spans": [
            {"label": "card_pan", "text": "4485 1267 3489 9012"},
            {"label": "private_person", "text": "Δημητρίου Στ."},
            {"label": "private_phone", "text": "2109876543"},
            {"label": "private_url", "text": "piraeusbank.gr/fraud-report"},
        ],
    },
    {
        "id": 23,
        "register": "bank_iban_request",
        "text": (
            "Alpha Bank — Επιβεβαίωση IBAN\n"
            "Πελάτης: Αγγελική Φραντζή\n"
            "ΑΦΜ: 156234897\n"
            "IBAN: GR16 0140 1010 1010 0000 1234 567\n"
            "Διεύθυνση: Σόλωνος 67, 10672 Αθήνα\n"
            "Email: a.frantzi@example.gr | Τηλ: 6932456789\n"
            "Έκδοση: 14/03/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Αγγελική Φραντζή"},
            {"label": "afm", "text": "156234897"},
            {"label": "iban_gr", "text": "GR16 0140 1010 1010 0000 1234 567"},
            {"label": "private_address", "text": "Σόλωνος 67, 10672 Αθήνα"},
            {"label": "private_email", "text": "a.frantzi@example.gr"},
            {"label": "private_phone", "text": "6932456789"},
            {"label": "private_date", "text": "14/03/2026"},
        ],
    },
    {
        "id": 24,
        "register": "card_verification_sms",
        "text": (
            "Ο κωδικός σας OTP για συναλλαγή €120 με κάρτα 5536 8912 4567 8901 "
            "(CVV2 234) είναι: 487213. Ισχύει 5 λεπτά. "
            "Μη μοιραστείτε με κανέναν. NBG Greece"
        ),
        "spans": [
            {"label": "card_pan", "text": "5536 8912 4567 8901"},
            {"label": "cvv", "text": "234"},
            {"label": "secret", "text": "487213"},
        ],
    },
    {
        "id": 25,
        "register": "loan_application",
        "text": (
            "Τράπεζα Πειραιώς — Αίτηση Δανείου\n"
            "Αιτών: Νίκος Σπυρίδων Παππαθανασόπουλος\n"
            "ΑΦΜ: 145678234 | ΑΜΚΑ: 09128034567\n"
            "ΑΔΤ: ΑΗ-873524\n"
            "Διεύθυνση: Πανεπιστημίου 18, 10672 Αθήνα\n"
            "Τηλ.: 6987654321 | Email: nikos.sp@example.com\n"
            "Ποσό: 50.000€ | Διάρκεια: 10 έτη\n"
            "Ημ. αίτησης: 25/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Νίκος Σπυρίδων Παππαθανασόπουλος"},
            {"label": "afm", "text": "145678234"},
            {"label": "amka", "text": "09128034567"},
            {"label": "adt", "text": "ΑΗ-873524"},
            {"label": "private_address", "text": "Πανεπιστημίου 18, 10672 Αθήνα"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_email", "text": "nikos.sp@example.com"},
            {"label": "private_date", "text": "25/04/2026"},
        ],
    },
]
