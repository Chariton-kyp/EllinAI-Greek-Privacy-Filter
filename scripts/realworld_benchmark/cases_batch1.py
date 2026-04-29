"""Real-world benchmark cases — Batch 1 (40 cases).

Hand-crafted realistic Greek prose covering 24 PII classes. All values are
fictional but follow canonical Greek/EU formats. Text is OOD from training
distribution: register variation (formal letters, SMS, technical logs,
medical referrals, court filings, etc.), Greek inflection diversity
(nominative/genitive/vocative), prefix variants, real-world punctuation
density.

Each case:
    id: int
    register: descriptive register tag
    text: full text passage
    spans: list of {label, text} — offsets computed by validator below.

Spans are stored as label+exact-text pairs. The build script validates
that each span text occurs verbatim in the case text and computes char
offsets. If a span text appears multiple times the first occurrence is
used; tag with "occurrence" to disambiguate.
"""
from __future__ import annotations

CASES = [
    # --- Tax / Government (1-5) ---
    {
        "id": 1,
        "register": "tax_form_letter",
        "text": (
            "Αξιότιμη κα Παπαδοπούλου,\n\n"
            "Η Διεύθυνση Φορολογίας ΔΟΥ Α' Αθηνών σας ενημερώνει ότι εκκρεμεί η δήλωση "
            "Ε1 για το φορολογικό έτος 2025. Παρακαλούμε προσέλθετε με ΑΦΜ 124356789, "
            "ΑΔΤ ΑΚ-734812 και αποδεικτικό ΑΜΚΑ 27098245678. Διεύθυνση κατοικίας: "
            "Ηπείρου 47, 11251 Αθήνα."
        ),
        "spans": [
            {"label": "private_person", "text": "Παπαδοπούλου"},
            {"label": "afm", "text": "124356789"},
            {"label": "adt", "text": "ΑΚ-734812"},
            {"label": "amka", "text": "27098245678"},
            {"label": "private_address", "text": "Ηπείρου 47, 11251 Αθήνα"},
        ],
    },
    {
        "id": 2,
        "register": "tax_sms_short",
        "text": "ΕΝΦΙΑ 2026: Πληρωμή έως 30/06/2026. ΑΦΜ: 087451209. Στοιχεία: gov.gr/enfia",
        "spans": [
            {"label": "private_date", "text": "30/06/2026"},
            {"label": "afm", "text": "087451209"},
            {"label": "private_url", "text": "gov.gr/enfia"},
        ],
    },
    {
        "id": 3,
        "register": "tax_office_email",
        "text": (
            "From: doy.athens@aade.gr\nTo: stergios.markou@example.gr\n"
            "Θέμα: Εκκρεμότητα ΦΠΑ\n\n"
            "Κύριε Μάρκου, η εταιρεία σας με ΓΕΜΗ 089451200000 και ΑΦΜ 094782315 "
            "οφείλει να υποβάλει την περιοδική δήλωση Φ2 έως την 25 Φεβρουαρίου 2026."
        ),
        "spans": [
            {"label": "private_email", "text": "doy.athens@aade.gr"},
            {"label": "private_email", "text": "stergios.markou@example.gr"},
            {"label": "private_person", "text": "Μάρκου"},
            {"label": "gemi", "text": "089451200000"},
            {"label": "afm", "text": "094782315"},
            {"label": "private_date", "text": "25 Φεβρουαρίου 2026"},
        ],
    },
    {
        "id": 4,
        "register": "tax_authority_record",
        "text": (
            "ΑΑΔΕ - Στοιχεία Φορολογουμένου\n"
            "Όνομα: Δημήτριος Στεφανίδης\n"
            "ΑΦΜ: 156234897 | ΑΜΚΑ: 03128956712 | ΑΔΤ: ΞΗ-456789\n"
            "Δ/νση: Κηφισίας 232, 14564 Κηφισιά"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτριος Στεφανίδης"},
            {"label": "afm", "text": "156234897"},
            {"label": "amka", "text": "03128956712"},
            {"label": "adt", "text": "ΞΗ-456789"},
            {"label": "private_address", "text": "Κηφισίας 232, 14564 Κηφισιά"},
        ],
    },
    {
        "id": 5,
        "register": "vat_number_query",
        "text": (
            "Παρακαλώ επιβεβαιώστε το ΑΦΜ της προμηθεύτριας εταιρείας 'Ελληνικά Τρόφιμα ΕΠΕ': "
            "ΑΦΜ 998123456, ΓΕΜΗ 145789300000."
        ),
        "spans": [
            {"label": "afm", "text": "998123456"},
            {"label": "gemi", "text": "145789300000"},
        ],
    },

    # --- Banking (6-12) ---
    {
        "id": 6,
        "register": "bank_transfer_email",
        "text": (
            "Η μεταφορά 2.500,00€ από τον λογαριασμό σας 5012-87654-321 ολοκληρώθηκε "
            "επιτυχώς προς IBAN GR9602601230000000845129003 του δικαιούχου Ιωάννης Ζαχαριάς."
        ),
        "spans": [
            {"label": "account_number", "text": "5012-87654-321"},
            {"label": "iban_gr", "text": "GR9602601230000000845129003"},
            {"label": "private_person", "text": "Ιωάννης Ζαχαριάς"},
        ],
    },
    {
        "id": 7,
        "register": "card_payment_sms",
        "text": "Χρέωση 89.99€ στην κάρτα σας 4716 8765 4321 9876 με CVV 327. Λήξη 09/29.",
        "spans": [
            {"label": "card_pan", "text": "4716 8765 4321 9876"},
            {"label": "cvv", "text": "327"},
        ],
    },
    {
        "id": 8,
        "register": "bank_statement",
        "text": (
            "Στοιχεία Πελάτη: Αναστασία Καραμπίνη\n"
            "Λογαριασμός: 0234-56789-101 | IBAN: GR4001101230000023456789101\n"
            "Τηλ. επικοινωνίας: 6944321567"
        ),
        "spans": [
            {"label": "private_person", "text": "Αναστασία Καραμπίνη"},
            {"label": "account_number", "text": "0234-56789-101"},
            {"label": "iban_gr", "text": "GR4001101230000023456789101"},
            {"label": "private_phone", "text": "6944321567"},
        ],
    },
    {
        "id": 9,
        "register": "card_authorization",
        "text": (
            "Έγκριση συναλλαγής Mastercard 5188 9234 5678 1234 (CVC2: 891) στο Skroutz, "
            "ποσό 145€. Κωδ. έγκρισης 7842-AX."
        ),
        "spans": [
            {"label": "card_pan", "text": "5188 9234 5678 1234"},
            {"label": "cvv", "text": "891"},
        ],
    },
    {
        "id": 10,
        "register": "iban_change_form",
        "text": (
            "Παρακαλώ ενημερώστε τον νέο IBAN GR1602601200000123456789012 για τη μηνιαία "
            "πληρωμή της Ελευθερίας Νικολαΐδου, ΑΦΜ 045672198."
        ),
        "spans": [
            {"label": "iban_gr", "text": "GR1602601200000123456789012"},
            {"label": "private_person", "text": "Ελευθερίας Νικολαΐδου"},
            {"label": "afm", "text": "045672198"},
        ],
    },
    {
        "id": 11,
        "register": "loan_application",
        "text": (
            "Αιτών: Παύλος Δημόπουλος, ΑΦΜ 234567891. Λογαριασμός μισθοδοσίας: 7012-34567-890. "
            "Μηνιαίο εισόδημα: 2.450€. Επικοινωνία: 6976543210, pavlos.dim@webmail.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Παύλος Δημόπουλος"},
            {"label": "afm", "text": "234567891"},
            {"label": "account_number", "text": "7012-34567-890"},
            {"label": "private_phone", "text": "6976543210"},
            {"label": "private_email", "text": "pavlos.dim@webmail.gr"},
        ],
    },
    {
        "id": 12,
        "register": "card_block_request",
        "text": (
            "Αξιότιμοι, ζητώ άμεση φραγή της Visa 4532 1098 7654 3210 λόγω απώλειας. "
            "Ονοματεπώνυμο: Σωτήρης Παναγιώτου, τηλ. 6987654321."
        ),
        "spans": [
            {"label": "card_pan", "text": "4532 1098 7654 3210"},
            {"label": "private_person", "text": "Σωτήρης Παναγιώτου"},
            {"label": "private_phone", "text": "6987654321"},
        ],
    },

    # --- Vehicles (13-18) ---
    {
        "id": 13,
        "register": "vehicle_insurance_policy",
        "text": (
            "Συμβόλαιο ασφάλισης οχήματος. Πινακίδα: ΥΗΕ-2384. Αρ. πλαισίου: WBAVD13526NJ54321. "
            "Ασφαλισμένος: Γιώργος Παππάς, δίπλωμα οδήγησης 845721369."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΥΗΕ-2384"},
            {"label": "vehicle_vin", "text": "WBAVD13526NJ54321"},
            {"label": "private_person", "text": "Γιώργος Παππάς"},
            {"label": "driver_license", "text": "845721369"},
        ],
    },
    {
        "id": 14,
        "register": "traffic_violation_notice",
        "text": (
            "Παράβαση Κ.Ο.Κ.: Όχημα με πινακίδα ΙΚΤ-4567, οδηγός Νικόλαος Αντωνίου, ΑΔΤ ΖΓ123456. "
            "Πρόστιμο 200€ έως 15 Μαΐου 2026."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΙΚΤ-4567"},
            {"label": "private_person", "text": "Νικόλαος Αντωνίου"},
            {"label": "adt", "text": "ΖΓ123456"},
            {"label": "private_date", "text": "15 Μαΐου 2026"},
        ],
    },
    {
        "id": 15,
        "register": "car_sale_agreement",
        "text": (
            "Αγοραπωλησία οχήματος μάρκας Toyota, αρ. πλαισίου JTDBR32E520123456, "
            "πινακίδα ΖΧΥ-8821. Πωλητής: Ευάγγελος Στεργίου (ΑΦΜ 156789432). Τιμή 9.500€."
        ),
        "spans": [
            {"label": "vehicle_vin", "text": "JTDBR32E520123456"},
            {"label": "license_plate", "text": "ΖΧΥ-8821"},
            {"label": "private_person", "text": "Ευάγγελος Στεργίου"},
            {"label": "afm", "text": "156789432"},
        ],
    },
    {
        "id": 16,
        "register": "driver_license_renewal",
        "text": (
            "Ανανέωση διπλώματος οδήγησης αρ. 234876591, κάτοχος Χριστίνα Παπαδέρου, "
            "ημερομηνία γέννησης 12 Ιανουαρίου 1978, ΑΜΚΑ 12017812345."
        ),
        "spans": [
            {"label": "driver_license", "text": "234876591"},
            {"label": "private_person", "text": "Χριστίνα Παπαδέρου"},
            {"label": "private_date", "text": "12 Ιανουαρίου 1978"},
            {"label": "amka", "text": "12017812345"},
        ],
    },
    {
        "id": 17,
        "register": "stolen_vehicle_report",
        "text": (
            "Δηλώθηκε κλοπή οχήματος Skoda Octavia, πινακίδα ΗΑΖ-9012, αρ. πλαισίου "
            "TMBJF41Z7B2098765 από την οδό Ομήρου 18, Παγκράτι."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΗΑΖ-9012"},
            {"label": "vehicle_vin", "text": "TMBJF41Z7B2098765"},
            {"label": "private_address", "text": "Ομήρου 18, Παγκράτι"},
        ],
    },
    {
        "id": 18,
        "register": "vehicle_kteo",
        "text": (
            "Πιστοποιητικό ΚΤΕΟ για όχημα ΥΧΑ-3478, αρ. πλαισίου WAUZZZ8VXAA123456. "
            "Επόμενος έλεγχος: 14/03/2027."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΥΧΑ-3478"},
            {"label": "vehicle_vin", "text": "WAUZZZ8VXAA123456"},
            {"label": "private_date", "text": "14/03/2027"},
        ],
    },

    # --- IT / Security (19-24) ---
    {
        "id": 19,
        "register": "it_incident_log",
        "text": (
            "[2026-04-28 14:35:21] WARN suspicious login from IP 78.45.123.67, MAC "
            "AA:BB:CC:DD:EE:01. User: alice@company.gr. Endpoint https://vpn.company.gr/login."
        ),
        "spans": [
            {"label": "ip_address", "text": "78.45.123.67"},
            {"label": "mac_address", "text": "AA:BB:CC:DD:EE:01"},
            {"label": "private_email", "text": "alice@company.gr"},
            {"label": "private_url", "text": "https://vpn.company.gr/login"},
        ],
    },
    {
        "id": 20,
        "register": "api_key_leak",
        "text": (
            "Ανιχνεύθηκε διαρροή API token tk_live_4eC39HqLyjWDarjtT1zdp7dc στο repo. "
            "Επικοινωνία με security@firm.gr για άμεση ανάκληση."
        ),
        "spans": [
            {"label": "secret", "text": "tk_live_4eC39HqLyjWDarjtT1zdp7dc"},
            {"label": "private_email", "text": "security@firm.gr"},
        ],
    },
    {
        "id": 21,
        "register": "system_admin_email",
        "text": (
            "Νέος server pinned at 192.168.10.45. Admin: admin.ops@netcorp.gr. "
            "Κωδ. πρόσβασης: P@ssw0rd!2026SecretXYZ. Εσωτερικό dashboard: https://internal.netcorp.gr/admin"
        ),
        "spans": [
            {"label": "ip_address", "text": "192.168.10.45"},
            {"label": "private_email", "text": "admin.ops@netcorp.gr"},
            {"label": "secret", "text": "P@ssw0rd!2026SecretXYZ"},
            {"label": "private_url", "text": "https://internal.netcorp.gr/admin"},
        ],
    },
    {
        "id": 22,
        "register": "device_inventory",
        "text": (
            "Inventory entry: Laptop ID DEV-2089, MAC FF:11:22:33:44:55, IP 10.0.5.123, "
            "registered to Σταυρούλα Δημητρίου (sdimitriou@dept.gr)."
        ),
        "spans": [
            {"label": "mac_address", "text": "FF:11:22:33:44:55"},
            {"label": "ip_address", "text": "10.0.5.123"},
            {"label": "private_person", "text": "Σταυρούλα Δημητρίου"},
            {"label": "private_email", "text": "sdimitriou@dept.gr"},
        ],
    },
    {
        "id": 23,
        "register": "vpn_creds_email",
        "text": (
            "Στοιχεία VPN: server=vpn-eu.acme.gr, username=jvelis, password=Tr0ub4dor&3!Greek2026. "
            "Πρόσβαση μέσω https://portal.acme.gr/sso."
        ),
        "spans": [
            {"label": "secret", "text": "Tr0ub4dor&3!Greek2026"},
            {"label": "private_url", "text": "https://portal.acme.gr/sso"},
        ],
    },
    {
        "id": 24,
        "register": "firewall_rule",
        "text": (
            "Allow inbound TCP/443 from 195.78.234.10 to 10.10.20.50, MAC source 00:1A:2B:3C:4D:5E. "
            "Approved by netops@company.gr."
        ),
        "spans": [
            {"label": "ip_address", "text": "195.78.234.10"},
            {"label": "ip_address", "text": "10.10.20.50"},
            {"label": "mac_address", "text": "00:1A:2B:3C:4D:5E"},
            {"label": "private_email", "text": "netops@company.gr"},
        ],
    },

    # --- Medical (25-30) ---
    {
        "id": 25,
        "register": "medical_referral",
        "text": (
            "Παραπεμπτικό για αιματολογικές εξετάσεις. Ασθενής: Αλέξανδρος Παρασκευόπουλος, "
            "ΑΜΚΑ 14076512345, ηλικίας 50 ετών. Διεύθυνση: Ευελπίδων 24, Κυψέλη. Τηλ.: 6932145678."
        ),
        "spans": [
            {"label": "private_person", "text": "Αλέξανδρος Παρασκευόπουλος"},
            {"label": "amka", "text": "14076512345"},
            {"label": "private_address", "text": "Ευελπίδων 24, Κυψέλη"},
            {"label": "private_phone", "text": "6932145678"},
        ],
    },
    {
        "id": 26,
        "register": "hospital_admission",
        "text": (
            "Εισαγωγή στον Ευαγγελισμό. Ασθενής: Μαρία-Ελένη Γεωργοπούλου (ΑΜΚΑ 23128945612). "
            "Συνοδός: Παναγιώτης Γεωργόπουλος, τηλ. 2107654321."
        ),
        "spans": [
            {"label": "private_person", "text": "Μαρία-Ελένη Γεωργοπούλου"},
            {"label": "amka", "text": "23128945612"},
            {"label": "private_person", "text": "Παναγιώτης Γεωργόπουλος"},
            {"label": "private_phone", "text": "2107654321"},
        ],
    },
    {
        "id": 27,
        "register": "prescription",
        "text": (
            "Συνταγή για: Ηλίας Σταματόπουλος, ΑΜΚΑ 09058723456. Φάρμακο: Atorvastatin 20mg, "
            "1 δισκίο/ημέρα. Επανεξέταση: 30 Σεπτεμβρίου 2026. Επικοινωνία: 6912345678."
        ),
        "spans": [
            {"label": "private_person", "text": "Ηλίας Σταματόπουλος"},
            {"label": "amka", "text": "09058723456"},
            {"label": "private_date", "text": "30 Σεπτεμβρίου 2026"},
            {"label": "private_phone", "text": "6912345678"},
        ],
    },
    {
        "id": 28,
        "register": "vaccination_record",
        "text": (
            "Αρχείο εμβολιασμού - ΑΜΚΑ: 18046512345 - Όνομα: Νίκος Παπαϊωάννου - "
            "Διεύθυνση: Λεωφ. Αλεξάνδρας 89, Αθήνα 11473."
        ),
        "spans": [
            {"label": "amka", "text": "18046512345"},
            {"label": "private_person", "text": "Νίκος Παπαϊωάννου"},
            {"label": "private_address", "text": "Λεωφ. Αλεξάνδρας 89, Αθήνα 11473"},
        ],
    },
    {
        "id": 29,
        "register": "lab_test_result_email",
        "text": (
            "From: lab.athens@bioiatriki.gr\n"
            "Αποτελέσματα εξετάσεων ασθενούς Ευαγγελία Καλλιακούδη (ΑΜΚΑ 30087812345). "
            "Διαθέσιμα στο https://patients.bioiatriki.gr/r/4abc123."
        ),
        "spans": [
            {"label": "private_email", "text": "lab.athens@bioiatriki.gr"},
            {"label": "private_person", "text": "Ευαγγελία Καλλιακούδη"},
            {"label": "amka", "text": "30087812345"},
            {"label": "private_url", "text": "https://patients.bioiatriki.gr/r/4abc123"},
        ],
    },
    {
        "id": 30,
        "register": "appointment_confirm_sms",
        "text": (
            "Ραντεβού 15:30 την Τρίτη 18/05/2026, Δρ. Καρρά. ΑΜΚΑ 25067843219. Διεύθυνση κλινικής: "
            "Δοϊράνης 12, Καλλιθέα. Τηλ. 2109876543."
        ),
        "spans": [
            {"label": "private_date", "text": "18/05/2026"},
            {"label": "private_person", "text": "Καρρά"},
            {"label": "amka", "text": "25067843219"},
            {"label": "private_address", "text": "Δοϊράνης 12, Καλλιθέα"},
            {"label": "private_phone", "text": "2109876543"},
        ],
    },

    # --- Mobile / IMEI / Passport (31-35) ---
    {
        "id": 31,
        "register": "lost_phone_report",
        "text": (
            "Δήλωση απώλειας κινητού iPhone 13, IMEI 354812095123456, χρώμα μπλε. "
            "Κάτοχος: Δέσποινα Λάππα, τηλ. αναφοράς 6987123456."
        ),
        "spans": [
            {"label": "imei", "text": "354812095123456"},
            {"label": "private_person", "text": "Δέσποινα Λάππα"},
            {"label": "private_phone", "text": "6987123456"},
        ],
    },
    {
        "id": 32,
        "register": "mobile_contract",
        "text": (
            "Συμβόλαιο κινητής Cosmote: συσκευή Samsung Galaxy S23 IMEI: 359876123456789. "
            "Συμβολαιούχος: Παύλος Καραβίτης, ΑΦΜ 167823945, αρ. SIM 6940987654."
        ),
        "spans": [
            {"label": "imei", "text": "359876123456789"},
            {"label": "private_person", "text": "Παύλος Καραβίτης"},
            {"label": "afm", "text": "167823945"},
            {"label": "private_phone", "text": "6940987654"},
        ],
    },
    {
        "id": 33,
        "register": "passport_application",
        "text": (
            "Αίτηση έκδοσης διαβατηρίου. Στοιχεία αιτούντος: Φωτεινή Καλογήρου, "
            "διαβατήριο AΒ4567321 (παλαιό), ημ. γέννησης 22 Ιουλίου 1990, "
            "διεύθυνση Σολωμού 14, Αθήνα 10683."
        ),
        "spans": [
            {"label": "private_person", "text": "Φωτεινή Καλογήρου"},
            {"label": "passport", "text": "AΒ4567321"},
            {"label": "private_date", "text": "22 Ιουλίου 1990"},
            {"label": "private_address", "text": "Σολωμού 14, Αθήνα 10683"},
        ],
    },
    {
        "id": 34,
        "register": "travel_visa_request",
        "text": (
            "Αίτημα visa για Καναδά. Διαβατήριο AK0982345, κάτοχος Λεωνίδας Σαμπάνης. "
            "Διάρκεια ταξιδιού: 03/06/2026 έως 28/06/2026."
        ),
        "spans": [
            {"label": "passport", "text": "AK0982345"},
            {"label": "private_person", "text": "Λεωνίδας Σαμπάνης"},
            {"label": "private_date", "text": "03/06/2026"},
            {"label": "private_date", "text": "28/06/2026"},
        ],
    },
    {
        "id": 35,
        "register": "device_warranty_email",
        "text": (
            "Εγγύηση συσκευής Apple iPad. IMEI/Serial: 358745612098765. "
            "Δικαιούχος: kostas.papan@gmail.com. Λήξη εγγύησης 02/12/2027."
        ),
        "spans": [
            {"label": "imei", "text": "358745612098765"},
            {"label": "private_email", "text": "kostas.papan@gmail.com"},
            {"label": "private_date", "text": "02/12/2027"},
        ],
    },

    # --- Employment / HR (36-40) ---
    {
        "id": 36,
        "register": "employment_contract",
        "text": (
            "Σύμβαση εργασίας μεταξύ ACME ΕΠΕ (ΓΕΜΗ 178945612000) και του Νεκτάριου Βασιλείου, "
            "ΑΦΜ 198765432, ΑΜΑ ΙΚΑ 9876543. Έναρξη: 1η Ιουνίου 2026. Αποδοχές: 1.450€ μηνιαίως."
        ),
        "spans": [
            {"label": "gemi", "text": "178945612000"},
            {"label": "private_person", "text": "Νεκτάριου Βασιλείου"},
            {"label": "afm", "text": "198765432"},
            {"label": "ama", "text": "9876543"},
            {"label": "private_date", "text": "1η Ιουνίου 2026"},
        ],
    },
    {
        "id": 37,
        "register": "hr_email_signature",
        "text": (
            "Με εκτίμηση,\nΣτέλιος Καραμπίνης\nHR Manager\n"
            "skarabinis@enterprise.gr\nΤηλ.: 210-9876543 | Κιν.: 6944112233\n"
            "Λεωφ. Κηφισίας 124, 11526 Αμπελόκηποι"
        ),
        "spans": [
            {"label": "private_person", "text": "Στέλιος Καραμπίνης"},
            {"label": "private_email", "text": "skarabinis@enterprise.gr"},
            {"label": "private_phone", "text": "210-9876543"},
            {"label": "private_phone", "text": "6944112233"},
            {"label": "private_address", "text": "Λεωφ. Κηφισίας 124, 11526 Αμπελόκηποι"},
        ],
    },
    {
        "id": 38,
        "register": "payslip",
        "text": (
            "Μισθοδοσία 04/2026. Εργαζόμενος: Σοφία Χρυσικού. ΑΜΑ ΙΚΑ: 5678901. "
            "ΑΦΜ: 234156789. Καθαρές αποδοχές 1.230,45€ στον IBAN GR2701401320132012345678901."
        ),
        "spans": [
            {"label": "private_person", "text": "Σοφία Χρυσικού"},
            {"label": "ama", "text": "5678901"},
            {"label": "afm", "text": "234156789"},
            {"label": "iban_gr", "text": "GR2701401320132012345678901"},
        ],
    },
    {
        "id": 39,
        "register": "job_application",
        "text": (
            "Βιογραφικό υποψηφίου Δημήτρης-Παύλος Βλάχος, dimvlachos@protonmail.com, 6951234567. "
            "Διαθέσιμος για συνέντευξη από 10/05/2026. Διεύθυνση: Ηρακλείου 88, Πειραιάς."
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτρης-Παύλος Βλάχος"},
            {"label": "private_email", "text": "dimvlachos@protonmail.com"},
            {"label": "private_phone", "text": "6951234567"},
            {"label": "private_date", "text": "10/05/2026"},
            {"label": "private_address", "text": "Ηρακλείου 88, Πειραιάς"},
        ],
    },
    {
        "id": 40,
        "register": "termination_notice",
        "text": (
            "Καταγγελία σύμβασης εργασίας προς τον κο Αθανάσιο Ζαχαριάδη (ΑΜΑ 4567890), "
            "ισχύει από 30 Ιουνίου 2026. Καταβολή αποζημίωσης στον IBAN GR0701101900190245678901234."
        ),
        "spans": [
            {"label": "private_person", "text": "Αθανάσιο Ζαχαριάδη"},
            {"label": "ama", "text": "4567890"},
            {"label": "private_date", "text": "30 Ιουνίου 2026"},
            {"label": "iban_gr", "text": "GR0701101900190245678901234"},
        ],
    },
]
