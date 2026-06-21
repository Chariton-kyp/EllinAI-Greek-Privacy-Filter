"""Greek PII Public Benchmark v1 — Part 2 (cases 26-50).

Banking continued (26-30), Court/Legal (31-40), HR/Employment (41-50).

All values synthetic. License: CC-BY-4.0.
"""
from __future__ import annotations

CASES = [
    # ============== BANKING continued (26-30) ==============
    {
        "id": 26,
        "register": "bank_statement_pdf_extract",
        "text": (
            "ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ\n"
            "Μηνιαίο Statement Λογαριασμού\n"
            "Δικαιούχος: Παύλος Γεωργιάδης\n"
            "Λογαριασμός: 1110-23456-78901-234\n"
            "IBAN: GR89 0110 1100 0000 1102 3456 789\n"
            "Περίοδος: 01/04/2026 - 30/04/2026\n"
            "Email: p.georgiadis@example.gr\n"
            "Υπόλοιπο: 12.450,67€"
        ),
        "spans": [
            {"label": "private_person", "text": "Παύλος Γεωργιάδης"},
            {"label": "account_number", "text": "1110-23456-78901-234"},
            {"label": "iban_gr", "text": "GR89 0110 1100 0000 1102 3456 789"},
            {"label": "private_date", "text": "01/04/2026"},
            {"label": "private_date", "text": "30/04/2026"},
            {"label": "private_email", "text": "p.georgiadis@example.gr"},
        ],
    },
    {
        "id": 27,
        "register": "bank_fraud_alert",
        "text": (
            "🚨 Eurobank Alert\n"
            "Ύποπτη συναλλαγή €1.200 από κάρτα 4485-1267-3489-9012 σε "
            "ξένο πάροχο. Επικοινωνήστε άμεσα.\n"
            "Δικαιούχος: Στέλιος Μαρίνος\n"
            "Τηλ: 2106789012 | https://eurobank.gr/fraud-report-form\n"
            "Server log IP: 185.142.78.231"
        ),
        "spans": [
            {"label": "card_pan", "text": "4485-1267-3489-9012"},
            {"label": "private_person", "text": "Στέλιος Μαρίνος"},
            {"label": "private_phone", "text": "2106789012"},
            {"label": "private_url", "text": "https://eurobank.gr/fraud-report-form"},
            {"label": "ip_address", "text": "185.142.78.231"},
        ],
    },
    {
        "id": 28,
        "register": "bank_password_reset",
        "text": (
            "Alpha Bank — Reset κωδικού\n"
            "Πελάτης: Δήμητρα Φιλίππου\n"
            "Email: dimitra.f@example.com\n"
            "Νέος προσωρινός κωδικός: TmpPass!2026X9k\n"
            "Λήγει: 12/05/2026\n"
            "Σύνδεση: alphabank.gr/login\n"
            "ΑΦΜ ταυτοποίησης: 234561289"
        ),
        "spans": [
            {"label": "private_person", "text": "Δήμητρα Φιλίππου"},
            {"label": "private_email", "text": "dimitra.f@example.com"},
            {"label": "secret", "text": "TmpPass!2026X9k"},
            {"label": "private_date", "text": "12/05/2026"},
            {"label": "private_url", "text": "alphabank.gr/login"},
            {"label": "afm", "text": "234561289"},
        ],
    },
    {
        "id": 29,
        "register": "bank_loan_decision",
        "text": (
            "Τράπεζα Πειραιώς — Απόφαση Στεγαστικού Δανείου\n"
            "Αιτών: Φωτεινή Καρανικόλα\n"
            "ΑΦΜ: 089123456\n"
            "ΑΜΚΑ: 22117234567\n"
            "Ποσό εγκριθέν: 150.000€ σε 25 έτη\n"
            "Επιτόκιο: 3.85% σταθερό 5 ετών\n"
            "IBAN εκταμίευσης: GR45 0172 0500 0000 5005 0099 887\n"
            "Ημ.: 30/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Φωτεινή Καρανικόλα"},
            {"label": "afm", "text": "089123456"},
            {"label": "amka", "text": "22117234567"},
            {"label": "iban_gr", "text": "GR45 0172 0500 0000 5005 0099 887"},
            {"label": "private_date", "text": "30/04/2026"},
        ],
    },
    {
        "id": 30,
        "register": "atm_card_lost_report",
        "text": (
            "Δήλωση Απώλειας Κάρτας\n"
            "Πελάτης: Νίκος Λάμπρου, ΑΔΤ ΑΖ-456712\n"
            "Λογαριασμός: 1100-99887-65432-111\n"
            "Κάρτα: 5536 7890 1234 5678 (CVV: 567)\n"
            "Τηλ.: 6932451768 | Email: n.lambrou@example.com\n"
            "Τόπος απώλειας: Αερολιμένας Αθηνών\n"
            "Ημ.: 02/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Νίκος Λάμπρου"},
            {"label": "adt", "text": "ΑΖ-456712"},
            {"label": "account_number", "text": "1100-99887-65432-111"},
            {"label": "card_pan", "text": "5536 7890 1234 5678"},
            {"label": "cvv", "text": "567"},
            {"label": "private_phone", "text": "6932451768"},
            {"label": "private_email", "text": "n.lambrou@example.com"},
            {"label": "private_date", "text": "02/05/2026"},
        ],
    },
    # ============== COURT / LEGAL (31-40) ==============
    {
        "id": 31,
        "register": "court_decision_first_instance",
        "text": (
            "ΜΟΝΟΜΕΛΕΣ ΠΡΩΤΟΔΙΚΕΙΟ ΑΘΗΝΩΝ — Απόφαση 1234/2026\n\n"
            "Ο κατηγορούμενος Νικόλαος Σπύρου Παπαθανασόπουλος του Αντωνίου, "
            "ΑΔΤ ΑΗ-873524, κάτοικος οδού Πανεπιστημίου 18, 10672 Αθήνα, "
            "καταδικάζεται σε χρηματική ποινή 5.000 ευρώ για παράβαση του "
            "Ν. 4624/2019 περί προστασίας προσωπικών δεδομένων.\n\n"
            "Η απόφαση εκδόθηκε στην έδρα της 24 Φεβρουαρίου 2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλαος Σπύρου Παπαθανασόπουλος"},
            {"label": "adt", "text": "ΑΗ-873524"},
            {"label": "private_address", "text": "Πανεπιστημίου 18, 10672 Αθήνα"},
            {"label": "private_date", "text": "24 Φεβρουαρίου 2026"},
        ],
    },
    {
        "id": 32,
        "register": "court_summons",
        "text": (
            "Πρωτοδικείο Αθηνών — Κλήση Μάρτυρα\n"
            "Καλείστε: Μαρία Γαβριήλ-Παπαδοπούλου\n"
            "ΑΔΤ: ΑΞ-456712\n"
            "Διεύθυνση: Λιοσίων 234, 10440 Αθήνα\n"
            "Τηλ.: 6987234561\n"
            "Δικάσιμος: 18/06/2026 ώρα 10:00\n"
            "Email επικοινωνίας: protodikeio.athens@example.gov.gr\n"
            "Αρ. φακέλου: 2026/AT-78912"
        ),
        "spans": [
            {"label": "private_person", "text": "Μαρία Γαβριήλ-Παπαδοπούλου"},
            {"label": "adt", "text": "ΑΞ-456712"},
            {"label": "private_address", "text": "Λιοσίων 234, 10440 Αθήνα"},
            {"label": "private_phone", "text": "6987234561"},
            {"label": "private_date", "text": "18/06/2026"},
            {"label": "private_email", "text": "protodikeio.athens@example.gov.gr"},
        ],
    },
    {
        "id": 33,
        "register": "lawyer_email_to_client",
        "text": (
            "From: dimitra.lawyer@firm.gr\n"
            "To: stergios.client@example.com\n"
            "Θέμα: Υπόθεση Α12345/2026\n\n"
            "Κύριε Στέργιο, η αντίδικη πλευρά ζήτησε αναβολή. "
            "Νέα δικάσιμος: 22/07/2026. Παρακαλώ φέρτε ταυτότητα "
            "(ΑΔΤ ΑΘ-123456) και ΑΦΜ 156782341. Διεύθυνση γραφείου: "
            "Σόλωνος 78, 10680 Αθήνα. Τηλ. 2103456712.\n\n"
            "Δήμητρα Παπαδάκη, Δικηγόρος"
        ),
        "spans": [
            {"label": "private_email", "text": "dimitra.lawyer@firm.gr"},
            {"label": "private_email", "text": "stergios.client@example.com"},
            {"label": "private_person", "text": "Στέργιο"},
            {"label": "private_date", "text": "22/07/2026"},
            {"label": "adt", "text": "ΑΘ-123456"},
            {"label": "afm", "text": "156782341"},
            {"label": "private_address", "text": "Σόλωνος 78, 10680 Αθήνα"},
            {"label": "private_phone", "text": "2103456712"},
            {"label": "private_person", "text": "Δήμητρα Παπαδάκη"},
        ],
    },
    {
        "id": 34,
        "register": "police_report",
        "text": (
            "Αστυνομικό Τμήμα Νέας Σμύρνης — Δελτίο Συμβάντος\n"
            "Αρ. πρωτ.: ΑΤ-2026-4567\n"
            "Παθών: Ευστράτιος Καρράς, ΑΔΤ ΑΕ-678912\n"
            "Όχημα: Toyota Yaris, πινακίδα ΥΑΘ-3456\n"
            "VIN: WDB2110421B345678\n"
            "Δίπλωμα οδήγησης κατηγορίας Β αρ. 234567891\n"
            "Συμβάν: Σύγκρουση 03/05/2026 18:45\n"
            "Τηλ.: 6932451890"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευστράτιος Καρράς"},
            {"label": "adt", "text": "ΑΕ-678912"},
            {"label": "license_plate", "text": "ΥΑΘ-3456"},
            {"label": "vehicle_vin", "text": "WDB2110421B345678"},
            {"label": "driver_license", "text": "234567891"},
            {"label": "private_date", "text": "03/05/2026"},
            {"label": "private_phone", "text": "6932451890"},
        ],
    },
    {
        "id": 35,
        "register": "court_witness_statement",
        "text": (
            "Κατάθεση Μάρτυρα — Πρωτοδικείο Πειραιά\n"
            "Όνομα: Σπυρίδων Καραμανλής\n"
            "Διεύθυνση: Δημοκρατίας 89, 18534 Πειραιάς\n"
            "ΑΔΤ: ΑΡ-345891 | ΑΦΜ: 067412598\n"
            "Επάγγελμα: Λογιστής\n"
            "Email: sp.karamanlis@example.gr\n"
            "Ημ. κατάθεσης: 14/04/2026\n"
            "Δικαστής: κ. Παπανικολάου"
        ),
        "spans": [
            {"label": "private_person", "text": "Σπυρίδων Καραμανλής"},
            {"label": "private_address", "text": "Δημοκρατίας 89, 18534 Πειραιάς"},
            {"label": "adt", "text": "ΑΡ-345891"},
            {"label": "afm", "text": "067412598"},
            {"label": "private_email", "text": "sp.karamanlis@example.gr"},
            {"label": "private_date", "text": "14/04/2026"},
            {"label": "private_person", "text": "Παπανικολάου"},
        ],
    },
    {
        "id": 36,
        "register": "civil_lawsuit_filing",
        "text": (
            "Αγωγή Αποζημίωσης — Μονομελές Πρωτοδικείο Θεσσαλονίκης\n"
            "Ενάγων: Ιωάννης Σαμαράς, ΑΦΜ 098234567\n"
            "Διεύθυνση: Εγνατίας 145, 54624 Θεσσαλονίκη\n"
            "Εναγόμενη: Helios Insurance ΑΕ, ΓΕΜΗ 234567800000\n"
            "Όχημα: Mercedes E220, ΛΣ-2345\n"
            "Ποσό αξίωσης: 25.000€ | Ημ.: 18/03/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννης Σαμαράς"},
            {"label": "afm", "text": "098234567"},
            {"label": "private_address", "text": "Εγνατίας 145, 54624 Θεσσαλονίκη"},
            {"label": "gemi", "text": "234567800000"},
            {"label": "license_plate", "text": "ΛΣ-2345"},
            {"label": "private_date", "text": "18/03/2026"},
        ],
    },
    {
        "id": 37,
        "register": "criminal_case_file",
        "text": (
            "Εισαγγελία Πρωτοδικών Αθηνών\n"
            "Αρ. φακέλου: ΕΠ-2026/789\n"
            "Κατηγορούμενος: Πέτρος Σπυρίδωνος Μαραγκός\n"
            "ΑΔΤ ΑΣ-789012\n"
            "Ημ.γέν: 15/02/1985\n"
            "Διεύθυνση: Καρόλου 34, 10437 Αθήνα\n"
            "Διπλ. οδήγησης 567891234\n"
            "Παράβαση: Άρθρο 235 ΠΚ"
        ),
        "spans": [
            {"label": "private_person", "text": "Πέτρος Σπυρίδωνος Μαραγκός"},
            {"label": "adt", "text": "ΑΣ-789012"},
            {"label": "private_date", "text": "15/02/1985"},
            {"label": "private_address", "text": "Καρόλου 34, 10437 Αθήνα"},
            {"label": "driver_license", "text": "567891234"},
        ],
    },
    {
        "id": 38,
        "register": "notary_property_deed",
        "text": (
            "Συμβολαιογραφική Πράξη Αρ. 4567/2026\n"
            "Αγοραστής: Ελένη Αναγνωστοπούλου, ΑΦΜ 145678234\n"
            "Πωλητής: Νικόλαος Παπαδόπουλος, ΑΦΜ 234567812\n"
            "Ακίνητο: Ηπείρου 56, 10682 Αθήνα\n"
            "Τίμημα: 245.000€\n"
            "IBAN καταβολής: GR16 0140 6500 6500 0011 4587 998\n"
            "Συμβολαιογράφος: Δρ. Γεώργιος Λάμπρου, Σόλωνος 23, 10672 Αθήνα\n"
            "Ημ. υπογραφής: 12/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ελένη Αναγνωστοπούλου"},
            {"label": "afm", "text": "145678234"},
            {"label": "private_person", "text": "Νικόλαος Παπαδόπουλος"},
            {"label": "afm", "text": "234567812"},
            {"label": "private_address", "text": "Ηπείρου 56, 10682 Αθήνα"},
            {"label": "iban_gr", "text": "GR16 0140 6500 6500 0011 4587 998"},
            {"label": "private_person", "text": "Γεώργιος Λάμπρου"},
            {"label": "private_address", "text": "Σόλωνος 23, 10672 Αθήνα"},
            {"label": "private_date", "text": "12/04/2026"},
        ],
    },
    {
        "id": 39,
        "register": "judicial_order_search",
        "text": (
            "Δικαστική Παραγγελία Έρευνας — Αρ. 567/2026\n"
            "Στόχος: ηλεκτρονικά έγγραφα\n"
            "Φερόμενος: Δημήτριος Καραμπίνας\n"
            "ΑΔΤ ΑΟ-345678 | ΑΦΜ 156782349\n"
            "ΠΑΠ: 615784923W24\n"
            "Διεύθυνση: Δημητρίου Γούναρη 12, 54622 Θεσσαλονίκη\n"
            "Server IP target: 78.45.123.89\n"
            "Email υπό έρευνα: karabinas.d@example.com\n"
            "Ημ.: 28/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτριος Καραμπίνας"},
            {"label": "adt", "text": "ΑΟ-345678"},
            {"label": "afm", "text": "156782349"},
            {"label": "pcn", "text": "615784923W24"},
            {"label": "private_address", "text": "Δημητρίου Γούναρη 12, 54622 Θεσσαλονίκη"},
            {"label": "ip_address", "text": "78.45.123.89"},
            {"label": "private_email", "text": "karabinas.d@example.com"},
            {"label": "private_date", "text": "28/04/2026"},
        ],
    },
    {
        "id": 40,
        "register": "civil_protection_order",
        "text": (
            "Ασφαλιστικά Μέτρα — Προσωρινή Διαταγή\n"
            "Αιτούσα: Αναστασία Παπανικολάου\n"
            "ΑΔΤ ΑΠ-234567 | Τηλ.: 6987456321\n"
            "Διεύθυνση: Παπανδρέου 14, 17122 Ν. Σμύρνη\n"
            "Καθ' ου: Σωτήριος Ν. Δράκος\n"
            "Τηλ.: 6932561234\n"
            "Απαγόρευση προσέγγισης 200 μέτρων.\n"
            "Ημ. έκδοσης: 25/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Αναστασία Παπανικολάου"},
            {"label": "adt", "text": "ΑΠ-234567"},
            {"label": "private_phone", "text": "6987456321"},
            {"label": "private_address", "text": "Παπανδρέου 14, 17122 Ν. Σμύρνη"},
            {"label": "private_person", "text": "Σωτήριος Ν. Δράκος"},
            {"label": "private_phone", "text": "6932561234"},
            {"label": "private_date", "text": "25/04/2026"},
        ],
    },
    # ============== HR / EMPLOYMENT (41-50) ==============
    {
        "id": 41,
        "register": "hr_new_hire_email",
        "text": (
            "From: maria.papadaki@energaki.gr\n"
            "To: hr-team@energaki.gr\n"
            "Θέμα: Νέα πρόσληψη - Πέτρου Στεφανίδη\n\n"
            "Σας ενημερώνω ότι ολοκληρώθηκε η πρόσληψη του κ. "
            "Πέτρου Στεφανίδη με ΑΦΜ 968448119, ΑΜΚΑ 09128034567, "
            "ΑΜΑ ΙΚΑ 7845612. Έναρξη 15/05/2026.\n"
            "Μισθοδοσία IBAN: GR08 7367 0710 8359 0002 4085 851\n"
            "Επικοινωνία: 6987654321\n\nΜαρία Παπαδάκη"
        ),
        "spans": [
            {"label": "private_email", "text": "maria.papadaki@energaki.gr"},
            {"label": "private_email", "text": "hr-team@energaki.gr"},
            {"label": "private_person", "text": "Πέτρου Στεφανίδη"},
            {"label": "afm", "text": "968448119"},
            {"label": "amka", "text": "09128034567"},
            {"label": "ama", "text": "7845612"},
            {"label": "private_date", "text": "15/05/2026"},
            {"label": "iban_gr", "text": "GR08 7367 0710 8359 0002 4085 851"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_person", "text": "Μαρία Παπαδάκη"},
        ],
    },
    {
        "id": 42,
        "register": "employment_contract",
        "text": (
            "ESHARES — Σύμβαση Εργασίας\n"
            "Εργαζόμενος: Αλέξανδρος Παππάς\n"
            "ΑΦΜ: 156234897 | ΑΜΑ ΙΚΑ: 8765432\n"
            "ΑΜΚΑ: 22078134567 | ΑΔΤ: ΑΓ-234567\n"
            "Θέση: Senior Software Engineer\n"
            "Μηνιαίος μισθός: 4.500€\n"
            "IBAN καταβολής: GR55 6878 0626 0735 1392 5393 073\n"
            "Έναρξη: 01/06/2026 | Δοκιμασία: 6 μήνες έως 30/11/2026\n"
            "Email: alex.papas@eshares.com | Κιν: 6987456321"
        ),
        "spans": [
            {"label": "private_person", "text": "Αλέξανδρος Παππάς"},
            {"label": "afm", "text": "156234897"},
            {"label": "ama", "text": "8765432"},
            {"label": "amka", "text": "22078134567"},
            {"label": "adt", "text": "ΑΓ-234567"},
            {"label": "iban_gr", "text": "GR55 6878 0626 0735 1392 5393 073"},
            {"label": "private_date", "text": "01/06/2026"},
            {"label": "private_date", "text": "30/11/2026"},
            {"label": "private_email", "text": "alex.papas@eshares.com"},
            {"label": "private_phone", "text": "6987456321"},
        ],
    },
    {
        "id": 43,
        "register": "payroll_slip",
        "text": (
            "Μισθοδοσία ΜΑΪΟΥ 2026\n"
            "Επωνυμία εταιρίας: TechCorp ΑΕ, ΓΕΜΗ 765432100000\n"
            "Εργαζόμενος: Κατερίνα Λιακουλάκου\n"
            "ΑΦΜ: 234561289 | ΑΜΚΑ: 17086534567\n"
            "ΑΜΑ ΙΚΑ: 5634127\n"
            "Καθαρός μισθός: 1.842,50€\n"
            "IBAN: GR38 6089 9116 2759 0225 1121 380\n"
            "Email: liakoulakou.k@techcorp.gr"
        ),
        "spans": [
            {"label": "gemi", "text": "765432100000"},
            {"label": "private_person", "text": "Κατερίνα Λιακουλάκου"},
            {"label": "afm", "text": "234561289"},
            {"label": "amka", "text": "17086534567"},
            {"label": "ama", "text": "5634127"},
            {"label": "iban_gr", "text": "GR38 6089 9116 2759 0225 1121 380"},
            {"label": "private_email", "text": "liakoulakou.k@techcorp.gr"},
        ],
    },
    {
        "id": 44,
        "register": "employee_devops_credentials",
        "text": (
            "Παραλαβή Λογαριασμών Νέου DevOps\n"
            "Όνομα: Φοίβος Καμπύλης\n"
            "Email: phoivos.kambylis@firm.gr\n"
            "Workstation MAC: 00:1A:2B:3C:4D:5E\n"
            "Server IP: 10.0.45.67\n"
            "AWS Access Key: AKIAIOSFODNN7EXAMPLE\n"
            "Slack workspace: firm.slack.com/team/devops\n"
            "Έναρξη: 18/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Φοίβος Καμπύλης"},
            {"label": "private_email", "text": "phoivos.kambylis@firm.gr"},
            {"label": "mac_address", "text": "00:1A:2B:3C:4D:5E"},
            {"label": "ip_address", "text": "10.0.45.67"},
            {"label": "secret", "text": "AKIAIOSFODNN7EXAMPLE"},
            {"label": "private_url", "text": "firm.slack.com/team/devops"},
            {"label": "private_date", "text": "18/05/2026"},
        ],
    },
    {
        "id": 45,
        "register": "hr_termination_letter",
        "text": (
            "Επιστολή Καταγγελίας Σύμβασης\n"
            "Εργοδότης: Maritime Services ΑΕ, ΓΕΜΗ 089451200000\n"
            "Εργαζόμενος: Ιωάννης Φραντζής\n"
            "ΑΦΜ 228618516 | ΑΜΚΑ 22078134567\n"
            "Ημ. λήξης: 31/05/2026\n"
            "Αποζημίωση: 8.500€\n"
            "IBAN: GR45 0172 0500 0000 5005 0099 887\n"
            "Email: i.frantzis@example.com"
        ),
        "spans": [
            {"label": "gemi", "text": "089451200000"},
            {"label": "private_person", "text": "Ιωάννης Φραντζής"},
            {"label": "afm", "text": "228618516"},
            {"label": "amka", "text": "22078134567"},
            {"label": "private_date", "text": "31/05/2026"},
            {"label": "iban_gr", "text": "GR45 0172 0500 0000 5005 0099 887"},
            {"label": "private_email", "text": "i.frantzis@example.com"},
        ],
    },
    {
        "id": 46,
        "register": "hr_remote_setup",
        "text": (
            "Setup Remote Worker — Νέος εργαζόμενος\n"
            "Όνομα: Άννα Κωνσταντινίδου\n"
            "Email: anna.k@firm.gr | Κινητό: 6932456789\n"
            "Laptop MAC: AA:BB:CC:DD:EE:FF\n"
            "VPN URL: https://vpn-eu.firm.gr/connect\n"
            "VPN password (αρχικό, αλλάξτε): VPN_init_2026!Secure\n"
            "Τηλ. IT: 2106543210"
        ),
        "spans": [
            {"label": "private_person", "text": "Άννα Κωνσταντινίδου"},
            {"label": "private_email", "text": "anna.k@firm.gr"},
            {"label": "private_phone", "text": "6932456789"},
            {"label": "mac_address", "text": "AA:BB:CC:DD:EE:FF"},
            {"label": "private_url", "text": "https://vpn-eu.firm.gr/connect"},
            {"label": "secret", "text": "VPN_init_2026!Secure"},
            {"label": "private_phone", "text": "2106543210"},
        ],
    },
    {
        "id": 47,
        "register": "expat_hire_documents",
        "text": (
            "Πρόσληψη Αλλοδαπού — Visa & Permits\n"
            "Όνομα: Marco Rossi (Italy)\n"
            "Διαβατήριο: YA4567823\n"
            "Άδεια διαμονής αρ.: GR-2026-RES-78901\n"
            "ΑΦΜ που εκδόθηκε: 412967086\n"
            "ΑΜΚΑ: 11067845612\n"
            "Διεύθυνση Αθήνας: Πατησίων 89, 10434 Αθήνα\n"
            "Κιν.: 6987234567\n"
            "Έναρξη: 22/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Marco Rossi"},
            {"label": "passport", "text": "YA4567823"},
            {"label": "afm", "text": "412967086"},
            {"label": "amka", "text": "11067845612"},
            {"label": "private_address", "text": "Πατησίων 89, 10434 Αθήνα"},
            {"label": "private_phone", "text": "6987234567"},
            {"label": "private_date", "text": "22/05/2026"},
        ],
    },
    {
        "id": 48,
        "register": "performance_review",
        "text": (
            "Αξιολόγηση Απόδοσης Q1 2026\n"
            "Εργαζόμενος: Σπύρος Παπαευσταθίου\n"
            "Email: spyros.papa@example.com | ΑΜΑ ΙΚΑ 4523189\n"
            "Manager: κα. Ελένη Ιωαννίδη (eleni.ioan@example.com)\n"
            "Bonus: 2.500€ → IBAN GR89 0110 1100 0000 1102 3456 789\n"
            "Επόμενη review: 15/07/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Σπύρος Παπαευσταθίου"},
            {"label": "private_email", "text": "spyros.papa@example.com"},
            {"label": "ama", "text": "4523189"},
            {"label": "private_person", "text": "Ελένη Ιωαννίδη"},
            {"label": "private_email", "text": "eleni.ioan@example.com"},
            {"label": "iban_gr", "text": "GR89 0110 1100 0000 1102 3456 789"},
            {"label": "private_date", "text": "15/07/2026"},
        ],
    },
    {
        "id": 49,
        "register": "freelancer_invoice",
        "text": (
            "Τιμολόγιο Παροχής Υπηρεσιών\n"
            "Εκδότης: Ευστράτιος Νικολαΐδης (freelancer)\n"
            "ΑΦΜ: 336791255 | ΓΕΜΗ ατομικής: 456789100000\n"
            "Παραλήπτης: Innovate Hellas ΑΕ, ΓΕΜΗ 234567800000\n"
            "Ποσό: 4.200€ + ΦΠΑ 24% = 5.208€\n"
            "Πληρωμή σε IBAN: GR61 3399 9040 8566 3345 5353 547\n"
            "Email: efstratios.n@example.gr | Τηλ: 6987654321\n"
            "Ημ. έκδοσης: 02/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευστράτιος Νικολαΐδης"},
            {"label": "afm", "text": "336791255"},
            {"label": "gemi", "text": "456789100000"},
            {"label": "gemi", "text": "234567800000"},
            {"label": "iban_gr", "text": "GR61 3399 9040 8566 3345 5353 547"},
            {"label": "private_email", "text": "efstratios.n@example.gr"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_date", "text": "02/05/2026"},
        ],
    },
    {
        "id": 50,
        "register": "salary_increase_letter",
        "text": (
            "Αύξηση Μισθού — TechHellas ΑΕ\n"
            "Προς: Δήμητρα Καλαμπόκη\n"
            "ΑΦΜ 098234567 | ΑΜΚΑ 22117234567\n"
            "Από 1η Ιουνίου 2026 ο μισθός σας αυξάνεται από 2.800€ σε 3.200€.\n"
            "Διπλ. οδήγησης 234567891 για το εταιρικό αυτοκίνητο.\n"
            "Email: dkalaboki@techhellas.gr"
        ),
        "spans": [
            {"label": "private_person", "text": "Δήμητρα Καλαμπόκη"},
            {"label": "afm", "text": "098234567"},
            {"label": "amka", "text": "22117234567"},
            {"label": "private_date", "text": "1η Ιουνίου 2026"},
            {"label": "driver_license", "text": "234567891"},
            {"label": "private_email", "text": "dkalaboki@techhellas.gr"},
        ],
    },
]
