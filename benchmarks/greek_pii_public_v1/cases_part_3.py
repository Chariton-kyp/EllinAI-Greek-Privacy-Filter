"""Greek PII Public Benchmark v1 — Part 3 (cases 51-75).

Customer Support (51-60), Insurance (61-70), Vehicle start (71-75).

All values synthetic. License: CC-BY-4.0.
"""
from __future__ import annotations

CASES = [
    # ============== CUSTOMER SUPPORT (51-60) ==============
    {
        "id": 51,
        "register": "support_chat_lost_phone",
        "text": (
            "Πελάτης: Έχασα το κινητό μου, μπορείτε να το μπλοκάρετε;\n"
            "ΙΜΕΙ: 354123456789012\n"
            "Αρ. γραμμής: 6987654321\n"
            "Όνομα: Στέφανος Καραντινός, ΑΦΜ 481461729\n"
            "Email: stefanos.k@example.com\n\n"
            "Agent: Ναι, σε λίγο θα γίνει block. Παρακαλώ επιβεβαιώστε ΑΔΤ ΑΕ-456712 για ταυτοποίηση."
        ),
        "spans": [
            {"label": "imei", "text": "354123456789012"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_person", "text": "Στέφανος Καραντινός"},
            {"label": "afm", "text": "481461729"},
            {"label": "private_email", "text": "stefanos.k@example.com"},
            {"label": "adt", "text": "ΑΕ-456712"},
        ],
    },
    {
        "id": 52,
        "register": "support_card_blocked",
        "text": (
            "Πελάτης: Η κάρτα μου ακυρώθηκε χωρίς λόγο! 4485-1267-3489-9012, "
            "από Πέμπτη.\n\n"
            "Agent: Καλημέρα κ. Δημητρίου. Δώστε μου ΑΦΜ ή λογαριασμό 1110-23456-78901-234.\n\n"
            "Πελάτης: ΑΦΜ 091234567. Γεννήθηκα 12/03/1985.\n\n"
            "Agent: Ευχαριστώ. Επανενεργοποίηση 18:00 σήμερα."
        ),
        "spans": [
            {"label": "card_pan", "text": "4485-1267-3489-9012"},
            {"label": "private_person", "text": "Δημητρίου"},
            {"label": "account_number", "text": "1110-23456-78901-234"},
            {"label": "afm", "text": "091234567"},
            {"label": "private_date", "text": "12/03/1985"},
        ],
    },
    {
        "id": 53,
        "register": "telecom_support_internet",
        "text": (
            "Cosmote — Διαμαρτυρία internet\n"
            "Όνομα: Νίκος Παπαλεωνίδας\n"
            "Αρ. γραμμής: 2106789012\n"
            "Router MAC: 00:1B:44:11:3A:B7\n"
            "Public IP: 95.67.231.45\n"
            "Email: nikos.papa@example.gr\n"
            "Διεύθυνση εγκατάστασης: Λεωφ. Κηφισίας 234, 14564 Κηφισιά\n"
            "Τηλεφωνική επαφή: 6932456789"
        ),
        "spans": [
            {"label": "private_person", "text": "Νίκος Παπαλεωνίδας"},
            {"label": "private_phone", "text": "2106789012"},
            {"label": "mac_address", "text": "00:1B:44:11:3A:B7"},
            {"label": "ip_address", "text": "95.67.231.45"},
            {"label": "private_email", "text": "nikos.papa@example.gr"},
            {"label": "private_address", "text": "Λεωφ. Κηφισίας 234, 14564 Κηφισιά"},
            {"label": "private_phone", "text": "6932456789"},
        ],
    },
    {
        "id": 54,
        "register": "ecommerce_refund",
        "text": (
            "Skroutz Helpdesk — Επιστροφή χρημάτων\n"
            "Αγορά αρ.: ORD-2026-789123\n"
            "Πελάτης: Άρτεμις Μαστροπαναγιωτάκη\n"
            "Email: artemis.m@example.com | Κιν.: 6987234567\n"
            "Επιστροφή 89,90€ στην κάρτα 4123 5678 9012 3456\n"
            "Διεύθυνση παράδοσης: Λάρισας 78, 41335 Λάρισα\n"
            "Ημ. αίτησης: 25/04/2026"
        ),
        "spans": [
            {"label": "account_number", "text": "ORD-2026-789123"},
            {"label": "private_person", "text": "Άρτεμις Μαστροπαναγιωτάκη"},
            {"label": "private_email", "text": "artemis.m@example.com"},
            {"label": "private_phone", "text": "6987234567"},
            {"label": "card_pan", "text": "4123 5678 9012 3456"},
            {"label": "private_address", "text": "Λάρισας 78, 41335 Λάρισα"},
            {"label": "private_date", "text": "25/04/2026"},
        ],
    },
    {
        "id": 55,
        "register": "support_account_recovery",
        "text": (
            "Helpdesk — Ανάκτηση Λογαριασμού\n"
            "Πελάτης: Δημήτρης Ζαχαρίας\n"
            "Email registration: dimitrios.z@example.gr\n"
            "Νέος προσωρινός κωδικός: Recv_2026X9!P4ss\n"
            "API key (αντικαταστήστε): sk_live_abc123def456ghi789\n"
            "Login URL: https://app.firm.gr/auth/recover\n"
            "Λήγει σε 1 ώρα."
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτρης Ζαχαρίας"},
            {"label": "private_email", "text": "dimitrios.z@example.gr"},
            {"label": "secret", "text": "Recv_2026X9!P4ss"},
            {"label": "secret", "text": "sk_live_abc123def456ghi789"},
            {"label": "private_url", "text": "https://app.firm.gr/auth/recover"},
        ],
    },
    {
        "id": 56,
        "register": "telecom_imei_dispute",
        "text": (
            "Vodafone — Αλλαγή κατόχου SIM\n"
            "Νέος κάτοχος: Ιωάννα Δασκαλάκη\n"
            "ΑΦΜ: 246606120 | ΑΔΤ ΑΗ-345671\n"
            "Παλαιός IMEI: 869012345678901\n"
            "Νέο κινητό IMEI: 357246810234567\n"
            "Αρ. γραμμής: 6912345678\n"
            "Email: i.daskalaki@example.com\n"
            "Ημ.: 14/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννα Δασκαλάκη"},
            {"label": "afm", "text": "246606120"},
            {"label": "adt", "text": "ΑΗ-345671"},
            {"label": "imei", "text": "869012345678901"},
            {"label": "imei", "text": "357246810234567"},
            {"label": "private_phone", "text": "6912345678"},
            {"label": "private_email", "text": "i.daskalaki@example.com"},
            {"label": "private_date", "text": "14/05/2026"},
        ],
    },
    {
        "id": 57,
        "register": "support_security_incident",
        "text": (
            "Internal Security Notice\n"
            "User: thanasis.admin@firm.gr\n"
            "Login attempts από IP 203.0.113.42 (suspicious)\n"
            "MAC of compromised laptop: AB:CD:EF:12:34:56\n"
            "Secret key που πρέπει να γίνει rotate: GHSA_token_abc123def456\n"
            "Ημ.: 28/04/2026"
        ),
        "spans": [
            {"label": "private_email", "text": "thanasis.admin@firm.gr"},
            {"label": "ip_address", "text": "203.0.113.42"},
            {"label": "mac_address", "text": "AB:CD:EF:12:34:56"},
            {"label": "secret", "text": "GHSA_token_abc123def456"},
            {"label": "private_date", "text": "28/04/2026"},
        ],
    },
    {
        "id": 58,
        "register": "support_phone_account_recovery",
        "text": (
            "Πελάτης: Δεν θυμάμαι password.\n"
            "Agent: Δώστε μου ΑΦΜ.\n"
            "Πελάτης: 156782341, ονομάζομαι Στέλιος Νικολαΐδης.\n"
            "Agent: Email στο sysrecord;\n"
            "Πελάτης: stelios.nikolaidis@example.com\n"
            "Agent: SMS code στο 6987456321 → 487213. Δώστε το όταν φτάσει."
        ),
        "spans": [
            {"label": "afm", "text": "156782341"},
            {"label": "private_person", "text": "Στέλιος Νικολαΐδης"},
            {"label": "private_email", "text": "stelios.nikolaidis@example.com"},
            {"label": "private_phone", "text": "6987456321"},
            {"label": "secret", "text": "487213"},
        ],
    },
    {
        "id": 59,
        "register": "support_complaint_email",
        "text": (
            "From: c.papadakis@example.com\n"
            "To: complaints@retailchain.gr\n"
            "Θέμα: Ελαττωματικό προϊόν\n\n"
            "Παράγγειλα στις 12/04/2026 (αρ. παραγγελίας ORD-456789) "
            "και έλαβα ελαττωματικό προϊόν. ΑΦΜ μου: 067412598. "
            "Ζητώ επιστροφή χρημάτων στην κάρτα 4567 8901 2345 6789 (CVV 893).\n\n"
            "Δρ. Χριστόφορος Παπαδάκης\n"
            "Τηλ.: 2106543210"
        ),
        "spans": [
            {"label": "private_email", "text": "c.papadakis@example.com"},
            {"label": "private_email", "text": "complaints@retailchain.gr"},
            {"label": "private_date", "text": "12/04/2026"},
            {"label": "account_number", "text": "ORD-456789"},
            {"label": "afm", "text": "067412598"},
            {"label": "card_pan", "text": "4567 8901 2345 6789"},
            {"label": "cvv", "text": "893"},
            {"label": "private_person", "text": "Χριστόφορος Παπαδάκης"},
            {"label": "private_phone", "text": "2106543210"},
        ],
    },
    {
        "id": 60,
        "register": "support_dense_multi_pii",
        "text": (
            "Έντυπο επικοινωνίας για ΓΕΜΗ 567812000000\n"
            "Επωνυμία: Δικηγορικό Γραφείο Παπαδημητρίου\n"
            "ΑΦΜ: 098765432\n"
            "Νόμιμος εκπρόσωπος: Νικόλαος Παπαδημητρίου, ΑΔΤ ΑΞ-456789\n"
            "Διεύθυνση: Σκουφά 23, 10672 Αθήνα\n"
            "Email: legal@papadimitriou-firm.gr | Τηλ: 2103456789\n"
            "Site: https://papadimitriou-firm.gr/contact\n"
            "Office IP: 192.168.1.100"
        ),
        "spans": [
            {"label": "gemi", "text": "567812000000"},
            {"label": "afm", "text": "098765432"},
            {"label": "private_person", "text": "Νικόλαος Παπαδημητρίου"},
            {"label": "adt", "text": "ΑΞ-456789"},
            {"label": "private_address", "text": "Σκουφά 23, 10672 Αθήνα"},
            {"label": "private_email", "text": "legal@papadimitriou-firm.gr"},
            {"label": "private_phone", "text": "2103456789"},
            {"label": "private_url", "text": "https://papadimitriou-firm.gr/contact"},
            {"label": "ip_address", "text": "192.168.1.100"},
        ],
    },
    # ============== INSURANCE (61-70) ==============
    {
        "id": 61,
        "register": "vehicle_insurance_policy",
        "text": (
            "ΕΘΝΙΚΗ ΑΣΦΑΛΙΣΤΙΚΗ — Συμβόλαιο Αυτοκινήτου\n"
            "Όχημα: Mercedes E220, Πινακίδα ΖΗΟ-7456\n"
            "VIN: WDB2110421B345678\n"
            "Ασφαλισμένος: Δημήτρης Καρβέλας\n"
            "ΑΦΜ: 067834521 | ΑΔΤ: ΞΗ-456789\n"
            "Τηλέφωνο: 6932451287\n"
            "Email: dkarvelas@example.gr\n"
            "Συμβόλαιο: 12-2026-098765\n"
            "Ισχύει: 01/06/2026 - 31/05/2027"
        ),
        "spans": [
            {"label": "license_plate", "text": "ΖΗΟ-7456"},
            {"label": "vehicle_vin", "text": "WDB2110421B345678"},
            {"label": "private_person", "text": "Δημήτρης Καρβέλας"},
            {"label": "afm", "text": "067834521"},
            {"label": "adt", "text": "ΞΗ-456789"},
            {"label": "private_phone", "text": "6932451287"},
            {"label": "private_email", "text": "dkarvelas@example.gr"},
            {"label": "account_number", "text": "12-2026-098765"},
            {"label": "private_date", "text": "01/06/2026"},
            {"label": "private_date", "text": "31/05/2027"},
        ],
    },
    {
        "id": 62,
        "register": "insurance_claim_accident",
        "text": (
            "Δήλωση Τροχαίου Ατυχήματος\n"
            "Ασφαλιστικό: ALLIANZ Hellas, ΓΕΜΗ 098712300000\n"
            "Παθών: Ηλίας Βασιλείου\n"
            "ΑΔΤ: ΑΖ-890123\n"
            "Όχημα: BMW 320d, ΥΥΖ-9012\n"
            "VIN: WBA8E1C50JK123456\n"
            "Διπλ. οδήγησης 678912345\n"
            "Ημ. ατυχήματος: 18/04/2026 17:30\n"
            "Τόπος: Λεωφ. Συγγρού & Φιξ\n"
            "Τηλ.: 6932456789"
        ),
        "spans": [
            {"label": "gemi", "text": "098712300000"},
            {"label": "private_person", "text": "Ηλίας Βασιλείου"},
            {"label": "adt", "text": "ΑΖ-890123"},
            {"label": "license_plate", "text": "ΥΥΖ-9012"},
            {"label": "vehicle_vin", "text": "WBA8E1C50JK123456"},
            {"label": "driver_license", "text": "678912345"},
            {"label": "private_date", "text": "18/04/2026"},
            {"label": "private_phone", "text": "6932456789"},
        ],
    },
    {
        "id": 63,
        "register": "health_insurance_renewal",
        "text": (
            "Generali Hellas — Ανανέωση Ιδιωτικής Υγείας\n"
            "Δικαιούχος: Νίκος Φραντζής\n"
            "ΑΦΜ: 481603429\n"
            "ΑΜΚΑ: 07066163165\n"
            "Email: n.frantzis@example.com\n"
            "Διεύθυνση: Πατησίων 178, 11251 Αθήνα\n"
            "Συμβόλαιο: HEALTH-2026-456789\n"
            "Πληρωμή: IBAN GR86 5128 0725 9354 1578 0181 154\n"
            "Ισχύει έως: 30/04/2027"
        ),
        "spans": [
            {"label": "private_person", "text": "Νίκος Φραντζής"},
            {"label": "afm", "text": "481603429"},
            {"label": "amka", "text": "07066163165"},
            {"label": "private_email", "text": "n.frantzis@example.com"},
            {"label": "private_address", "text": "Πατησίων 178, 11251 Αθήνα"},
            {"label": "account_number", "text": "HEALTH-2026-456789"},
            {"label": "iban_gr", "text": "GR86 5128 0725 9354 1578 0181 154"},
            {"label": "private_date", "text": "30/04/2027"},
        ],
    },
    {
        "id": 64,
        "register": "home_insurance_quote",
        "text": (
            "Interamerican — Προσφορά Ασφάλισης Κατοικίας\n"
            "Ιδιοκτήτης: Σοφία Λεμπέση\n"
            "ΑΦΜ: 473893268 | ΑΔΤ: ΑΞ-234567\n"
            "Διεύθυνση κατοικίας: Αλεξάνδρας 132, 11522 Αθήνα\n"
            "Τετραγωνικά: 95τμ\n"
            "Έτος κατασκευής: 2010\n"
            "Ετήσιο ασφάλιστρο: 380€\n"
            "Email: sophia.l@example.gr | Τηλ: 6987234561"
        ),
        "spans": [
            {"label": "private_person", "text": "Σοφία Λεμπέση"},
            {"label": "afm", "text": "473893268"},
            {"label": "adt", "text": "ΑΞ-234567"},
            {"label": "private_address", "text": "Αλεξάνδρας 132, 11522 Αθήνα"},
            {"label": "private_email", "text": "sophia.l@example.gr"},
            {"label": "private_phone", "text": "6987234561"},
        ],
    },
    {
        "id": 65,
        "register": "vehicle_insurance_full_claim",
        "text": (
            "Εθνική Ασφαλιστική — Αίτηση Αποζημίωσης\n"
            "Ασφαλισμένος: Νικόλαος Παπαϊωάννου\n"
            "ΑΦΜ: 982734374 | Διπλ. οδήγησης κατηγορίας Β αρ. 345678912\n"
            "Όχημα: Volkswagen Passat, ΖΕΗ-7890\n"
            "VIN: WVWZZZ1JZXW123456\n"
            "Ζημιά: εμπρός προφυλακτήρας\n"
            "Συμβόλαιο: 12-2025-456789\n"
            "IBAN επιστροφής: GR10 6251 5459 2505 4477 5422 296\n"
            "Email: n.papaioan@example.gr | Κιν: 6932567890"
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλαος Παπαϊωάννου"},
            {"label": "afm", "text": "982734374"},
            {"label": "driver_license", "text": "345678912"},
            {"label": "license_plate", "text": "ΖΕΗ-7890"},
            {"label": "vehicle_vin", "text": "WVWZZZ1JZXW123456"},
            {"label": "account_number", "text": "12-2025-456789"},
            {"label": "iban_gr", "text": "GR10 6251 5459 2505 4477 5422 296"},
            {"label": "private_email", "text": "n.papaioan@example.gr"},
            {"label": "private_phone", "text": "6932567890"},
        ],
    },
    {
        "id": 66,
        "register": "travel_insurance",
        "text": (
            "Ταξιδιωτική Ασφάλιση — Bookings Hellas\n"
            "Ασφαλισμένος: Αικατερίνη Παπακωνσταντίνου\n"
            "Διαβατήριο: ΑΕ7234567\n"
            "ΑΦΜ: 045678912\n"
            "Προορισμός: Παρίσι, Γαλλία\n"
            "Ημ. ταξιδιού: 15/06/2026 - 22/06/2026\n"
            "Email: aikaterini.p@example.gr | Κιν: 6987456321\n"
            "Συμβόλαιο: TRV-2026-456789"
        ),
        "spans": [
            {"label": "private_person", "text": "Αικατερίνη Παπακωνσταντίνου"},
            {"label": "passport", "text": "ΑΕ7234567"},
            {"label": "afm", "text": "045678912"},
            {"label": "private_date", "text": "15/06/2026"},
            {"label": "private_date", "text": "22/06/2026"},
            {"label": "private_email", "text": "aikaterini.p@example.gr"},
            {"label": "private_phone", "text": "6987456321"},
            {"label": "account_number", "text": "TRV-2026-456789"},
        ],
    },
    {
        "id": 67,
        "register": "life_insurance_application",
        "text": (
            "Aiώνια ΑΕ — Αίτηση Ασφάλισης Ζωής\n"
            "Αιτών: Δημήτριος Στεφανίδης\n"
            "Ημ.γέν: 14/06/1985 | ΑΜΚΑ 14068550012\n"
            "ΑΦΜ: 639430158 | ΑΔΤ ΞΗ-678123\n"
            "Επάγγελμα: Δικηγόρος\n"
            "Δικαιούχος αποζημίωσης: Άννα Στεφανίδου (σύζυγος)\n"
            "ΑΦΜ συζύγου: 434402105\n"
            "Email: dim.stefanidis@example.com\n"
            "Ημ. αίτησης: 12/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτριος Στεφανίδης"},
            {"label": "private_date", "text": "14/06/1985"},
            {"label": "amka", "text": "14068550012"},
            {"label": "afm", "text": "639430158"},
            {"label": "adt", "text": "ΞΗ-678123"},
            {"label": "private_person", "text": "Άννα Στεφανίδου"},
            {"label": "afm", "text": "434402105"},
            {"label": "private_email", "text": "dim.stefanidis@example.com"},
            {"label": "private_date", "text": "12/05/2026"},
        ],
    },
    {
        "id": 68,
        "register": "insurance_call_log",
        "text": (
            "Call Log — ALLIANZ Helpline\n"
            "00:14:23 — Caller 6987234567 (Παύλος Δράκος)\n"
            "Συμβόλαιο: AUTO-2025-345678\n"
            "Όχημα ΛΣΑ-8901, VIN MNTBJK21Z1B345678\n"
            "Παράπονο: αύξηση ασφαλίστρου\n"
            "ΑΦΜ ταυτοποίησης: 098234561\n"
            "Email follow-up: paulos.d@example.gr"
        ),
        "spans": [
            {"label": "private_phone", "text": "6987234567"},
            {"label": "private_person", "text": "Παύλος Δράκος"},
            {"label": "account_number", "text": "AUTO-2025-345678"},
            {"label": "license_plate", "text": "ΛΣΑ-8901"},
            {"label": "vehicle_vin", "text": "MNTBJK21Z1B345678"},
            {"label": "afm", "text": "098234561"},
            {"label": "private_email", "text": "paulos.d@example.gr"},
        ],
    },
    {
        "id": 69,
        "register": "insurance_payment_reminder",
        "text": (
            "Eurolife FFH — Υπενθύμιση Πληρωμής\n"
            "Πελάτης: Ευφροσύνη Ντόκα\n"
            "Συμβόλαιο: HEALTH-345678\n"
            "Ποσό: 245€ έως 30/05/2026\n"
            "Πληρωμή σε IBAN: GR23 0652 3669 3815 0339 2579 025\n"
            "Με κάρτα: 4567-8901-2345-6789 (CVV: 234)\n"
            "Email: efrosini.n@example.com | Τηλ: 6912345678"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευφροσύνη Ντόκα"},
            {"label": "account_number", "text": "HEALTH-345678"},
            {"label": "private_date", "text": "30/05/2026"},
            {"label": "iban_gr", "text": "GR23 0652 3669 3815 0339 2579 025"},
            {"label": "card_pan", "text": "4567-8901-2345-6789"},
            {"label": "cvv", "text": "234"},
            {"label": "private_email", "text": "efrosini.n@example.com"},
            {"label": "private_phone", "text": "6912345678"},
        ],
    },
    {
        "id": 70,
        "register": "insurance_broker_quote",
        "text": (
            "Insurance Broker Hellas — Προσφορά Ασφάλισης Φλώτας\n"
            "Πελάτης: Logistics Express ΑΕ, ΓΕΜΗ 007326820896\n"
            "ΑΦΜ: 087451209\n"
            "Διεύθυνση: ΒΙΠΕ Σίνδου 234, 57400 Σίνδος\n"
            "Στόλος: 15 οχήματα (ΥΑΘ-3456 έως ΥΑΘ-3470)\n"
            "Επικοινωνία: Δημήτρης Χατζηγιάννης, broker.dim@firm.gr, 6987234567\n"
            "Πρόταση ισχύει έως: 31/05/2026"
        ),
        "spans": [
            {"label": "gemi", "text": "007326820896"},
            {"label": "afm", "text": "087451209"},
            {"label": "private_address", "text": "ΒΙΠΕ Σίνδου 234, 57400 Σίνδος"},
            {"label": "license_plate", "text": "ΥΑΘ-3456"},
            {"label": "license_plate", "text": "ΥΑΘ-3470"},
            {"label": "private_person", "text": "Δημήτρης Χατζηγιάννης"},
            {"label": "private_email", "text": "broker.dim@firm.gr"},
            {"label": "private_phone", "text": "6987234567"},
            {"label": "private_date", "text": "31/05/2026"},
        ],
    },
    # ============== VEHICLE / DRIVING (71-75, συνέχεια στο part 4) ==============
    {
        "id": 71,
        "register": "vehicle_registration",
        "text": (
            "Υπουργείο Μεταφορών — Άδεια Κυκλοφορίας\n"
            "Όχημα: Toyota Corolla 2020\n"
            "Πινακίδα: ΡΥΕ-2345\n"
            "VIN: JTDBL40E10J123456\n"
            "Ιδιοκτήτης: Μιχαήλ Παππάς\n"
            "ΑΦΜ: 151760154 | ΑΔΤ ΑΛ-456789\n"
            "Διεύθυνση: Δημητρίου Γούναρη 12, 54622 Θεσσαλονίκη\n"
            "Πρώτη κυκλοφορία: 15/03/2020"
        ),
        "spans": [
            {"label": "license_plate", "text": "ΡΥΕ-2345"},
            {"label": "vehicle_vin", "text": "JTDBL40E10J123456"},
            {"label": "private_person", "text": "Μιχαήλ Παππάς"},
            {"label": "afm", "text": "151760154"},
            {"label": "adt", "text": "ΑΛ-456789"},
            {"label": "private_address", "text": "Δημητρίου Γούναρη 12, 54622 Θεσσαλονίκη"},
            {"label": "private_date", "text": "15/03/2020"},
        ],
    },
    {
        "id": 72,
        "register": "driver_license_renewal",
        "text": (
            "Διεύθυνση Συγκοινωνιών — Ανανέωση Διπλώματος\n"
            "Όνομα: Σπυρίδων Δημητρόπουλος\n"
            "Δίπλωμα οδήγησης κατηγορίας ΑΜ-Β αρ. 991876733\n"
            "ΑΦΜ: 730797666 | ΑΜΚΑ 01106468616\n"
            "ΑΔΤ: ΑΣ-789012\n"
            "Ισχύει έως: 14/06/2031\n"
            "Email: spyros.d@example.gr | Τηλ: 6987456321\n"
            "Διεύθυνση: Σόλωνος 78, 10680 Αθήνα"
        ),
        "spans": [
            {"label": "private_person", "text": "Σπυρίδων Δημητρόπουλος"},
            {"label": "driver_license", "text": "991876733"},
            {"label": "afm", "text": "730797666"},
            {"label": "amka", "text": "01106468616"},
            {"label": "adt", "text": "ΑΣ-789012"},
            {"label": "private_date", "text": "14/06/2031"},
            {"label": "private_email", "text": "spyros.d@example.gr"},
            {"label": "private_phone", "text": "6987456321"},
            {"label": "private_address", "text": "Σόλωνος 78, 10680 Αθήνα"},
        ],
    },
    {
        "id": 73,
        "register": "ktep_inspection",
        "text": (
            "ΚΤΕΟ — Πιστοποιητικό Ελέγχου\n"
            "Όχημα: Honda Civic, Πινακίδα ΚΗΞ-4567\n"
            "VIN: 1HGBH41JXMN123456\n"
            "Ιδιοκτήτης: Νίκος Χατζημιχαήλ\n"
            "ΑΦΜ: 337944100\n"
            "Δίπλωμα οδήγησης 678912345\n"
            "Ημ. ελέγχου: 22/04/2026 | Επόμενος: 22/04/2028\n"
            "Email: n.hatzi@example.com"
        ),
        "spans": [
            {"label": "license_plate", "text": "ΚΗΞ-4567"},
            {"label": "vehicle_vin", "text": "1HGBH41JXMN123456"},
            {"label": "private_person", "text": "Νίκος Χατζημιχαήλ"},
            {"label": "afm", "text": "337944100"},
            {"label": "driver_license", "text": "678912345"},
            {"label": "private_date", "text": "22/04/2026"},
            {"label": "private_date", "text": "22/04/2028"},
            {"label": "private_email", "text": "n.hatzi@example.com"},
        ],
    },
    {
        "id": 74,
        "register": "traffic_fine",
        "text": (
            "Δημοτική Αστυνομία Αθηνών — Κλήση Παράβασης\n"
            "Πινακίδα: ΥΥΖ-9012\n"
            "Παράβαση: Παρκάρισμα σε χώρο ΑΜΕΑ\n"
            "Πρόστιμο: 200€\n"
            "Παραβάτης (κάτοχος): Αναστασία Παπαδημητρίου\n"
            "ΑΦΜ: 839521095 | Δίπλ. οδήγησης κατηγορίας Β αρ. 345678912\n"
            "Διεύθυνση: Πατησίων 234, 11251 Αθήνα\n"
            "Ημ. παράβασης: 30/04/2026 14:23"
        ),
        "spans": [
            {"label": "license_plate", "text": "ΥΥΖ-9012"},
            {"label": "private_person", "text": "Αναστασία Παπαδημητρίου"},
            {"label": "afm", "text": "839521095"},
            {"label": "driver_license", "text": "345678912"},
            {"label": "private_address", "text": "Πατησίων 234, 11251 Αθήνα"},
            {"label": "private_date", "text": "30/04/2026"},
        ],
    },
    {
        "id": 75,
        "register": "car_dealership_sale",
        "text": (
            "ΕΛΛΗΝΟΑΥΤΟ ΑΕ — Πώληση Καινούργιου Αυτοκινήτου\n"
            "Αγοραστής: Ευθύμιος Καραβίτης\n"
            "ΑΦΜ: 891468360 | ΑΔΤ ΑΘ-123456\n"
            "Διεύθυνση: Εθνικής Αντιστάσεως 89, 16562 Γλυφάδα\n"
            "Όχημα: Tesla Model 3, VIN 5YJ3E1EA9NF123456, Πινακίδα ΥΑΧ-5678\n"
            "Τιμή: 48.500€\n"
            "Πληρωμή: IBAN GR76 2889 7810 9134 3008 3774 035\n"
            "Email: e.karavitis@example.com | Τηλ: 6932561234"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευθύμιος Καραβίτης"},
            {"label": "afm", "text": "891468360"},
            {"label": "adt", "text": "ΑΘ-123456"},
            {"label": "private_address", "text": "Εθνικής Αντιστάσεως 89, 16562 Γλυφάδα"},
            {"label": "vehicle_vin", "text": "5YJ3E1EA9NF123456"},
            {"label": "license_plate", "text": "ΥΑΧ-5678"},
            {"label": "iban_gr", "text": "GR76 2889 7810 9134 3008 3774 035"},
            {"label": "private_email", "text": "e.karavitis@example.com"},
            {"label": "private_phone", "text": "6932561234"},
        ],
    },
]
