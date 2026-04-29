"""Real-world benchmark cases — Batch 2 (40 cases).

Focus: classes underserved by batch 1 — pcn (0), passport (2), card_pan
(3), cvv (2), driver_license (2), imei (3), ama (3), adt (3),
mac_address (3), secret (3), gemi (3), account_number (3),
vehicle_vin (4), iban_gr (5), license_plate (5), ip_address (5),
private_url (5).
"""
from __future__ import annotations

CASES = [
    # --- PCN (Personal Citizen Number) — 8 cases ---
    {
        "id": 41,
        "register": "citizen_id_form",
        "text": (
            "Στοιχεία πολίτη: Ελένη Σταυρίδου. Προσωπικός Αριθμός Πολίτη (ΠΑΠ): 124356789X42. "
            "Διεύθυνση: Παπαφλέσσα 23, 18537 Πειραιάς."
        ),
        "spans": [
            {"label": "private_person", "text": "Ελένη Σταυρίδου"},
            {"label": "pcn", "text": "124356789X42"},
            {"label": "private_address", "text": "Παπαφλέσσα 23, 18537 Πειραιάς"},
        ],
    },
    {
        "id": 42,
        "register": "pcn_letter",
        "text": (
            "Αξιότιμε κ. Παππά, ο νέος σας Προσωπικός Αριθμός Πολίτη είναι 987654321A07 "
            "και αντικαθιστά τον προηγούμενο. Διατηρήστε τον για κάθε επικοινωνία με το Δημόσιο."
        ),
        "spans": [
            {"label": "private_person", "text": "Παππά"},
            {"label": "pcn", "text": "987654321A07"},
        ],
    },
    {
        "id": 43,
        "register": "egov_login",
        "text": (
            "Σύνδεση gov.gr: PCN 456712389B91, εμφανίζονται οι υπηρεσίες σας. "
            "Επικοινωνία helpdesk@gov.gr."
        ),
        "spans": [
            {"label": "pcn", "text": "456712389B91"},
            {"label": "private_email", "text": "helpdesk@gov.gr"},
        ],
    },
    {
        "id": 44,
        "register": "social_benefit_application",
        "text": (
            "Αίτηση επιδόματος. Δικαιούχος: Νικολέτα Καρρά, ΠΑΠ 234561987Z45, ΑΜΚΑ 14056712345. "
            "Καταβολή στον IBAN GR1102601200000045671234567."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικολέτα Καρρά"},
            {"label": "pcn", "text": "234561987Z45"},
            {"label": "amka", "text": "14056712345"},
            {"label": "iban_gr", "text": "GR1102601200000045671234567"},
        ],
    },
    {
        "id": 45,
        "register": "pcn_change_request",
        "text": (
            "Αίτημα αλλαγής στοιχείων. Παλαιός ΠΑΠ: 567823491K22, Νέος ΠΑΠ: 567823491K88. "
            "Δικαιολογητικό: αντίγραφο ΑΔΤ ΞΘ-789012."
        ),
        "spans": [
            {"label": "pcn", "text": "567823491K22"},
            {"label": "pcn", "text": "567823491K88"},
            {"label": "adt", "text": "ΞΘ-789012"},
        ],
    },
    {
        "id": 46,
        "register": "pension_record",
        "text": (
            "Φάκελος συνταξιούχου: Ιωάννης Μαρκόπουλος, ΠΑΠ 678912345W18. "
            "Σύνταξη πληρώθηκε στις 28 Φεβρουαρίου 2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννης Μαρκόπουλος"},
            {"label": "pcn", "text": "678912345W18"},
            {"label": "private_date", "text": "28 Φεβρουαρίου 2026"},
        ],
    },
    {
        "id": 47,
        "register": "covid_certificate",
        "text": (
            "Πιστοποιητικό υγείας. Όνομα: Δημήτρης Παπαδάκης. ΠΑΠ: 098765432Q03. ΑΜΚΑ: 16078512345."
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτρης Παπαδάκης"},
            {"label": "pcn", "text": "098765432Q03"},
            {"label": "amka", "text": "16078512345"},
        ],
    },
    {
        "id": 48,
        "register": "government_letter",
        "text": (
            "Από: Υπουργείο Εσωτερικών. Προς: Αναστάσιο Λάμπρου. ΠΑΠ ταυτοποίησης 345672198M65. "
            "Παρακαλώ προσέλθετε στο ΚΕΠ Ηλιούπολης με ΑΔΤ ΧΑ891234."
        ),
        "spans": [
            {"label": "private_person", "text": "Αναστάσιο Λάμπρου"},
            {"label": "pcn", "text": "345672198M65"},
            {"label": "adt", "text": "ΧΑ891234"},
        ],
    },

    # --- Passport (49-54) ---
    {
        "id": 49,
        "register": "border_control_log",
        "text": (
            "Έλεγχος διαβατηρίων Σχηματάρι. Επιβάτης Anna Petridi, διαβατήριο AΓ7654321, "
            "πτήση A3-672, αναχώρηση 18:45."
        ),
        "spans": [
            {"label": "private_person", "text": "Anna Petridi"},
            {"label": "passport", "text": "AΓ7654321"},
        ],
    },
    {
        "id": 50,
        "register": "embassy_appointment",
        "text": (
            "Ραντεβού στην Πρεσβεία ΗΠΑ για visa. Διαβατήριο: AΡ4567812. Όνομα: Στράτος Λέκκας. "
            "Ώρα 11:00, ημ. 12 Ιουλίου 2026."
        ),
        "spans": [
            {"label": "passport", "text": "AΡ4567812"},
            {"label": "private_person", "text": "Στράτος Λέκκας"},
            {"label": "private_date", "text": "12 Ιουλίου 2026"},
        ],
    },
    {
        "id": 51,
        "register": "passport_lost_report",
        "text": (
            "Αναφορά απώλειας διαβατηρίου AB1234567 ιδιοκτησίας Καλλιόπης Σακελλαρίου. "
            "Δηλώθηκε στο ΑΤ Συντάγματος, αρ. δήλωσης 4567/2026."
        ),
        "spans": [
            {"label": "passport", "text": "AB1234567"},
            {"label": "private_person", "text": "Καλλιόπης Σακελλαρίου"},
        ],
    },
    {
        "id": 52,
        "register": "hotel_checkin",
        "text": (
            "Check-in Hotel Grande Bretagne. Επώνυμο: Καραμανλής. Διαβατήριο AC0987654. "
            "Δωμάτιο 412. Στοιχεία επικοινωνίας: nikoskaramanlis@yahoo.gr"
        ),
        "spans": [
            {"label": "private_person", "text": "Καραμανλής"},
            {"label": "passport", "text": "AC0987654"},
            {"label": "private_email", "text": "nikoskaramanlis@yahoo.gr"},
        ],
    },
    {
        "id": 53,
        "register": "id_doc_compare",
        "text": (
            "Αντιπαραβολή στοιχείων: Διαβατήριο AΕ8901234, ΑΔΤ ΞΞ-901234, ΑΦΜ 156789012. "
            "Όνομα: Παναγιώτης Σταματίου."
        ),
        "spans": [
            {"label": "passport", "text": "AΕ8901234"},
            {"label": "adt", "text": "ΞΞ-901234"},
            {"label": "afm", "text": "156789012"},
            {"label": "private_person", "text": "Παναγιώτης Σταματίου"},
        ],
    },
    {
        "id": 54,
        "register": "passport_renewal_email",
        "text": (
            "Παρελήφθη η αίτηση ανανέωσης διαβατηρίου AΗ5678901. Στοιχεία: Γιάννα Στράφορη "
            "(giannastrafori@hotmail.com), τηλ. 6948765432. Παραλαβή: 22/06/2026."
        ),
        "spans": [
            {"label": "passport", "text": "AΗ5678901"},
            {"label": "private_person", "text": "Γιάννα Στράφορη"},
            {"label": "private_email", "text": "giannastrafori@hotmail.com"},
            {"label": "private_phone", "text": "6948765432"},
            {"label": "private_date", "text": "22/06/2026"},
        ],
    },

    # --- Card / CVV — payment scenarios (55-62) ---
    {
        "id": 55,
        "register": "online_purchase_confirm",
        "text": (
            "Επιβεβαίωση αγοράς από Public.gr. Ποσό: 245.50€. Κάρτα Visa: 4929 1234 5678 9012, "
            "CVV2: 419. Παράδοση: Μεσογείων 354, 15341 Αγία Παρασκευή."
        ),
        "spans": [
            {"label": "card_pan", "text": "4929 1234 5678 9012"},
            {"label": "cvv", "text": "419"},
            {"label": "private_address", "text": "Μεσογείων 354, 15341 Αγία Παρασκευή"},
        ],
    },
    {
        "id": 56,
        "register": "card_fraud_alert",
        "text": (
            "Ειδοποίηση απάτης: συναλλαγή 2.000€ από κάρτα 5412 9876 5432 1098 (CVV 287) "
            "από IP 91.182.45.67. Παρακαλώ καλέστε στο 18181."
        ),
        "spans": [
            {"label": "card_pan", "text": "5412 9876 5432 1098"},
            {"label": "cvv", "text": "287"},
            {"label": "ip_address", "text": "91.182.45.67"},
        ],
    },
    {
        "id": 57,
        "register": "subscription_signup",
        "text": (
            "Νέα συνδρομή Netflix. Κάτοχος: Νικόλαος Παπαδημητρίου. Κάρτα 4485 7821 6543 2109, "
            "CVC 504. Email: npapad@gmail.com."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλαος Παπαδημητρίου"},
            {"label": "card_pan", "text": "4485 7821 6543 2109"},
            {"label": "cvv", "text": "504"},
            {"label": "private_email", "text": "npapad@gmail.com"},
        ],
    },
    {
        "id": 58,
        "register": "refund_request",
        "text": (
            "Επιστροφή χρημάτων στην κάρτα 5234 6789 1098 7654 (3-ψήφιος 162). "
            "Δικαιούχος: Σοφία Νικολαΐδου, IBAN GR8302601230000098712345678."
        ),
        "spans": [
            {"label": "card_pan", "text": "5234 6789 1098 7654"},
            {"label": "cvv", "text": "162"},
            {"label": "private_person", "text": "Σοφία Νικολαΐδου"},
            {"label": "iban_gr", "text": "GR8302601230000098712345678"},
        ],
    },
    {
        "id": 59,
        "register": "atm_card_request",
        "text": (
            "Νέα χρεωστική κάρτα 4921 5678 9012 3456 με CVV 738 παραδίδεται στη διεύθυνση "
            "Ναυαρίνου 8, 10680 Αθήνα. Παραλήπτης: Παύλος Δημόπουλος."
        ),
        "spans": [
            {"label": "card_pan", "text": "4921 5678 9012 3456"},
            {"label": "cvv", "text": "738"},
            {"label": "private_address", "text": "Ναυαρίνου 8, 10680 Αθήνα"},
            {"label": "private_person", "text": "Παύλος Δημόπουλος"},
        ],
    },
    {
        "id": 60,
        "register": "card_pan_only_receipt",
        "text": (
            "Απόδειξη πληρωμής - τέλη κυκλοφορίας 230€. Κάρτα ****-****-****-9876 "
            "(πλήρης 5290 1234 8765 9876)."
        ),
        "spans": [
            {"label": "card_pan", "text": "5290 1234 8765 9876"},
        ],
    },
    {
        "id": 61,
        "register": "ecommerce_invoice",
        "text": (
            "Τιμολόγιο #INV-2026-04567. Πελάτης: ΑΦΜ 234567891, Διονύσιος Σαμαράς. "
            "Πληρωμή: Mastercard 5403 2109 8765 4321 / CVV 951."
        ),
        "spans": [
            {"label": "afm", "text": "234567891"},
            {"label": "private_person", "text": "Διονύσιος Σαμαράς"},
            {"label": "card_pan", "text": "5403 2109 8765 4321"},
            {"label": "cvv", "text": "951"},
        ],
    },
    {
        "id": 62,
        "register": "card_expired_form",
        "text": (
            "Αντικατάσταση κάρτας. Παλαιός αριθμός: 4716 0000 1111 2222. "
            "Νέα κάρτα: 4716 0000 1111 9999, CVV 333."
        ),
        "spans": [
            {"label": "card_pan", "text": "4716 0000 1111 2222"},
            {"label": "card_pan", "text": "4716 0000 1111 9999"},
            {"label": "cvv", "text": "333"},
        ],
    },

    # --- GEMI / Company (63-67) ---
    {
        "id": 63,
        "register": "company_filing",
        "text": (
            "Υποβολή ισολογισμού 2025 για την εταιρεία Hellenic Tech Ltd, ΓΕΜΗ 198765400000, "
            "ΑΦΜ 998876543. Νόμιμος εκπρόσωπος Δημήτρης Καραντώνης."
        ),
        "spans": [
            {"label": "gemi", "text": "198765400000"},
            {"label": "afm", "text": "998876543"},
            {"label": "private_person", "text": "Δημήτρης Καραντώνης"},
        ],
    },
    {
        "id": 64,
        "register": "b2b_contract",
        "text": (
            "Σύμβαση συνεργασίας μεταξύ AlphaCorp ΑΕ (ΓΕΜΗ 234561200000) και BetaServices ΕΠΕ "
            "(ΓΕΜΗ 345672300000). Διάρκεια: 24 μήνες από 01/04/2026."
        ),
        "spans": [
            {"label": "gemi", "text": "234561200000"},
            {"label": "gemi", "text": "345672300000"},
            {"label": "private_date", "text": "01/04/2026"},
        ],
    },
    {
        "id": 65,
        "register": "company_registry_search",
        "text": (
            "Αναζήτηση μητρώου: 'Παπαδόπουλος και Σια ΟΕ'. ΓΕΜΗ 156789300000. Έδρα: "
            "Πατησίων 87, 10434 Αθήνα. Επικοινωνία: info@papadopoulos-oe.gr."
        ),
        "spans": [
            {"label": "gemi", "text": "156789300000"},
            {"label": "private_address", "text": "Πατησίων 87, 10434 Αθήνα"},
            {"label": "private_email", "text": "info@papadopoulos-oe.gr"},
        ],
    },
    {
        "id": 66,
        "register": "shareholder_letter",
        "text": (
            "Προς τους μετόχους της Mediterranean Foods ΑΕ (ΓΕΜΗ 087654300000). Γενική Συνέλευση "
            "30 Ιουνίου 2026, 10:00. Παρουσία ΑΔΤ ΑΖ-456789 του προέδρου Γεώργιου Καρρά."
        ),
        "spans": [
            {"label": "gemi", "text": "087654300000"},
            {"label": "private_date", "text": "30 Ιουνίου 2026"},
            {"label": "adt", "text": "ΑΖ-456789"},
            {"label": "private_person", "text": "Γεώργιου Καρρά"},
        ],
    },
    {
        "id": 67,
        "register": "company_dissolution",
        "text": (
            "Διάλυση εταιρείας Pelopon Imports ΕΕ, ΓΕΜΗ 145678500000, σύμφωνα με απόφαση 1245/2026 "
            "του ΓΕΜΗ. Εκκαθαριστής: Παύλος Νικολάου."
        ),
        "spans": [
            {"label": "gemi", "text": "145678500000"},
            {"label": "private_person", "text": "Παύλος Νικολάου"},
        ],
    },

    # --- Driver License + ADT (68-72) ---
    {
        "id": 68,
        "register": "driver_license_revocation",
        "text": (
            "Αφαίρεση διπλώματος οδήγησης 567812340 για 6 μήνες λόγω παράβασης. "
            "Κάτοχος Στέφανος Παπαντωνίου, ΑΔΤ ΖΥ-345678."
        ),
        "spans": [
            {"label": "driver_license", "text": "567812340"},
            {"label": "private_person", "text": "Στέφανος Παπαντωνίου"},
            {"label": "adt", "text": "ΖΥ-345678"},
        ],
    },
    {
        "id": 69,
        "register": "police_report_id",
        "text": (
            "Καταγραφή στοιχείων: ΑΔΤ ΑΗ712389. Δίπλωμα οδήγησης ΒΓ-456789. "
            "Όνομα: Σταύρος Λιναρδάκης. Ώρα ελέγχου: 23:45."
        ),
        "spans": [
            {"label": "adt", "text": "ΑΗ712389"},
            {"label": "driver_license", "text": "ΒΓ-456789"},
            {"label": "private_person", "text": "Σταύρος Λιναρδάκης"},
        ],
    },
    {
        "id": 70,
        "register": "id_renewal_form",
        "text": (
            "Ανανέωση ταυτότητας. Στοιχεία: Παρασκευή Ζαχαρίου, παλαιά ΑΔΤ ΞΛ234567, "
            "νέα ΑΔΤ ΧΞ891234. Δικαιολογητικά παρελήφθησαν."
        ),
        "spans": [
            {"label": "private_person", "text": "Παρασκευή Ζαχαρίου"},
            {"label": "adt", "text": "ΞΛ234567"},
            {"label": "adt", "text": "ΧΞ891234"},
        ],
    },
    {
        "id": 71,
        "register": "lost_dl_application",
        "text": (
            "Αίτηση αντίγραφου διπλώματος οδήγησης. Κάτοχος: Νικόλας Γιαννακόπουλος. "
            "Αρ. διπλώματος: 098712345. ΑΦΜ: 234567812. Τηλ. 6987456123."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλας Γιαννακόπουλος"},
            {"label": "driver_license", "text": "098712345"},
            {"label": "afm", "text": "234567812"},
            {"label": "private_phone", "text": "6987456123"},
        ],
    },
    {
        "id": 72,
        "register": "court_summons",
        "text": (
            "Κλήση μάρτυρα στο Μονομελές Πλημμελειοδικείο. Όνομα: Ευάγγελος Πετρίδης. "
            "ΑΔΤ: ΘΗ-678912. Ημ. δικασίμου: 15/09/2026, ώρα 09:30."
        ),
        "spans": [
            {"label": "private_person", "text": "Ευάγγελος Πετρίδης"},
            {"label": "adt", "text": "ΘΗ-678912"},
            {"label": "private_date", "text": "15/09/2026"},
        ],
    },

    # --- IMEI + MAC (73-77) ---
    {
        "id": 73,
        "register": "tech_support_ticket",
        "text": (
            "Ticket #34567 — συσκευή IMEI 868923054123456 αδυνατεί να συνδεθεί στο WiFi. "
            "MAC interface 5C:F9:38:AB:CD:01. User: kpapazafiri@firm.gr."
        ),
        "spans": [
            {"label": "imei", "text": "868923054123456"},
            {"label": "mac_address", "text": "5C:F9:38:AB:CD:01"},
            {"label": "private_email", "text": "kpapazafiri@firm.gr"},
        ],
    },
    {
        "id": 74,
        "register": "phone_blacklist",
        "text": (
            "Καταχώριση σε μαύρη λίστα: IMEI 357823195486732 (κλεμμένο). "
            "Αρ. δήλωσης: 8912/2026, ΑΤ Πατησίων."
        ),
        "spans": [
            {"label": "imei", "text": "357823195486732"},
        ],
    },
    {
        "id": 75,
        "register": "router_provisioning",
        "text": (
            "Νέο router εγκατεστημένο στη διεύθυνση Νηρηίδων 12, Νέα Ιωνία. "
            "MAC: 00:1B:21:C4:5E:78. Φιλικό όνομα: home-router-aris."
        ),
        "spans": [
            {"label": "private_address", "text": "Νηρηίδων 12, Νέα Ιωνία"},
            {"label": "mac_address", "text": "00:1B:21:C4:5E:78"},
        ],
    },
    {
        "id": 76,
        "register": "mobile_imei_log",
        "text": (
            "Λίστα συσκευών εργαζομένων: Αντώνης (IMEI 354987612345678), "
            "Χρήστος (IMEI 359876543210987)."
        ),
        "spans": [
            {"label": "private_person", "text": "Αντώνης"},
            {"label": "imei", "text": "354987612345678"},
            {"label": "private_person", "text": "Χρήστος"},
            {"label": "imei", "text": "359876543210987"},
        ],
    },
    {
        "id": 77,
        "register": "wifi_access_log",
        "text": (
            "Connect log: device MAC 02:42:AC:11:00:05 from IP 172.16.5.23 at 15:34. "
            "Authenticated user maria.kar@uni-athens.gr."
        ),
        "spans": [
            {"label": "mac_address", "text": "02:42:AC:11:00:05"},
            {"label": "ip_address", "text": "172.16.5.23"},
            {"label": "private_email", "text": "maria.kar@uni-athens.gr"},
        ],
    },

    # --- Account Number (78-80) ---
    {
        "id": 78,
        "register": "joint_account_form",
        "text": (
            "Άνοιγμα κοινού λογαριασμού. Συγκάτοχοι: Μαρία Παπαδά (ΑΦΜ 187654321), "
            "Δημήτρης Παπαδάς (ΑΦΜ 187654322). Αρ. λογαριασμού 0234-78901-456."
        ),
        "spans": [
            {"label": "private_person", "text": "Μαρία Παπαδά"},
            {"label": "afm", "text": "187654321"},
            {"label": "private_person", "text": "Δημήτρης Παπαδάς"},
            {"label": "afm", "text": "187654322"},
            {"label": "account_number", "text": "0234-78901-456"},
        ],
    },
    {
        "id": 79,
        "register": "account_balance_query",
        "text": (
            "Υπόλοιπο για λογαριασμό 5601-23456-789: 4.872,33€. Στοιχεία κατόχου: "
            "Φίλιππος Καρέλλας, τηλ. 6912348567."
        ),
        "spans": [
            {"label": "account_number", "text": "5601-23456-789"},
            {"label": "private_person", "text": "Φίλιππος Καρέλλας"},
            {"label": "private_phone", "text": "6912348567"},
        ],
    },
    {
        "id": 80,
        "register": "salary_deposit_notice",
        "text": (
            "Κατάθεση μισθοδοσίας 1.350€ στον λογαριασμό 8123-45678-012 του Παύλου Καρρά "
            "(ΑΜΑ ΙΚΑ 6789012). Επιβεβαίωση στο payroll@enterprise.gr."
        ),
        "spans": [
            {"label": "account_number", "text": "8123-45678-012"},
            {"label": "private_person", "text": "Παύλου Καρρά"},
            {"label": "ama", "text": "6789012"},
            {"label": "private_email", "text": "payroll@enterprise.gr"},
        ],
    },
]
