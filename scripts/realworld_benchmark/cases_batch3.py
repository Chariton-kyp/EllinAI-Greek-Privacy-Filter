"""Real-world benchmark cases — Batch 3 (40 cases).

Focus: classes still under 8 — secret (3), ama (4), private_url (5),
account_number (6), imei (7), license_plate (5), vehicle_vin (4),
driver_license (5), ip_address (7), iban_gr (7), mac_address (6).
Adds register diversity: real estate, education, legal, customer
support, social media, government letters.
"""
from __future__ import annotations

CASES = [
    # --- Secret heavy (81-86) ---
    {
        "id": 81,
        "register": "github_secret_alert",
        "text": (
            "GitHub Secret Scanning Alert: AWS_ACCESS_KEY_ID=AKMOIOSFODNN7EXAMPLE "
            "exposed in commit. Owner: dev.ops@payments.gr. Revoke at https://aws.amazon.com/iam."
        ),
        "spans": [
            {"label": "secret", "text": "AKMOIOSFODNN7EXAMPLE"},
            {"label": "private_email", "text": "dev.ops@payments.gr"},
            {"label": "private_url", "text": "https://aws.amazon.com/iam"},
        ],
    },
    {
        "id": 82,
        "register": "stripe_webhook",
        "text": (
            "Stripe webhook endpoint signing secret: wbsec_3K8bQc7sXm9V0aBcDeFgHi2jKlMnOpQr. "
            "Configure στο dashboard https://dashboard.stripe.com/webhooks."
        ),
        "spans": [
            {"label": "secret", "text": "wbsec_3K8bQc7sXm9V0aBcDeFgHi2jKlMnOpQr"},
            {"label": "private_url", "text": "https://dashboard.stripe.com/webhooks"},
        ],
    },
    {
        "id": 83,
        "register": "ssh_keys_share",
        "text": (
            "Παράδοση SSH credentials στον νέο dev. Private key passphrase: "
            "MySecretP@ss2026!Greek#prod. Repository: https://gitlab.greek-co.gr/infra/keys."
        ),
        "spans": [
            {"label": "secret", "text": "MySecretP@ss2026!Greek#prod"},
            {"label": "private_url", "text": "https://gitlab.greek-co.gr/infra/keys"},
        ],
    },
    {
        "id": 84,
        "register": "jwt_token_log",
        "text": (
            "JWT token issued: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummysig. "
            "Issuer: https://auth.platform.gr/jwt."
        ),
        "spans": [
            {"label": "secret", "text": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummysig"},
            {"label": "private_url", "text": "https://auth.platform.gr/jwt"},
        ],
    },
    {
        "id": 85,
        "register": "db_password_change",
        "text": (
            "Νέος κωδικός βάσης δεδομένων: Database#2026Postgres$Pass! "
            "Μην τον μοιράζεστε. Επικοινωνία dba@firm.gr."
        ),
        "spans": [
            {"label": "secret", "text": "Database#2026Postgres$Pass!"},
            {"label": "private_email", "text": "dba@firm.gr"},
        ],
    },
    {
        "id": 86,
        "register": "internal_doc_secret",
        "text": (
            "Confluence article: production API_KEY=ProdK3y_a4b8c2d6e0f1g5h9i3j7. "
            "Restrict to access@company.gr."
        ),
        "spans": [
            {"label": "secret", "text": "ProdK3y_a4b8c2d6e0f1g5h9i3j7"},
            {"label": "private_email", "text": "access@company.gr"},
        ],
    },

    # --- AMA / Social Security (87-92) ---
    {
        "id": 87,
        "register": "ama_card_renewal",
        "text": (
            "Αίτηση ανανέωσης βιβλιαρίου ΙΚΑ. Δικαιούχος: Ευστάθιος Σαμαράς. "
            "ΑΜΑ ΙΚΑ: 4567823. ΑΜΚΑ: 12056712345. Διεύθυνση: Θηβών 23, Πετρούπολη."
        ),
        "spans": [
            {"label": "private_person", "text": "Ευστάθιος Σαμαράς"},
            {"label": "ama", "text": "4567823"},
            {"label": "amka", "text": "12056712345"},
            {"label": "private_address", "text": "Θηβών 23, Πετρούπολη"},
        ],
    },
    {
        "id": 88,
        "register": "ika_doctor_visit",
        "text": (
            "Καρτέλα ιατρικής επίσκεψης. ΑΜΑ ΙΚΑ ασθενούς: 3456789. Ιατρός: "
            "Δρ. Παναγιώτα Κουτρά. Συνταγή: Lansoprazole."
        ),
        "spans": [
            {"label": "ama", "text": "3456789"},
            {"label": "private_person", "text": "Παναγιώτα Κουτρά"},
        ],
    },
    {
        "id": 89,
        "register": "unemployment_benefit",
        "text": (
            "Επίδομα ανεργίας ΟΑΕΔ. Αριθμ. Μητρώου Ασφάλισης: 9876543. "
            "Δικαιούχος: Ανδρέας Λύκος, ΑΦΜ 165432897, IBAN GR1402601500000001234567812."
        ),
        "spans": [
            {"label": "ama", "text": "9876543"},
            {"label": "private_person", "text": "Ανδρέας Λύκος"},
            {"label": "afm", "text": "165432897"},
            {"label": "iban_gr", "text": "GR1402601500000001234567812"},
        ],
    },
    {
        "id": 90,
        "register": "pension_letter",
        "text": (
            "Από: ΕΦΚΑ. Σας πληροφορούμε ότι το αίτημα σύνταξης για ΑΜΑ 7890123 "
            "εγκρίθηκε. Καταβολή στις 30 Ιουλίου 2026."
        ),
        "spans": [
            {"label": "ama", "text": "7890123"},
            {"label": "private_date", "text": "30 Ιουλίου 2026"},
        ],
    },
    {
        "id": 91,
        "register": "social_security_form",
        "text": (
            "Έντυπο εγγραφής στην ασφάλιση. Στοιχεία εργοδότη: Χρήστος Καραντώνης, "
            "ΑΜΑ Εργοδότη 2345678. Έναρξη απασχόλησης: 15/03/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Χρήστος Καραντώνης"},
            {"label": "ama", "text": "2345678"},
            {"label": "private_date", "text": "15/03/2026"},
        ],
    },
    {
        "id": 92,
        "register": "claim_compensation",
        "text": (
            "Αίτηση αποζημίωσης. ΑΜΑ ΙΚΑ: 8901234, ΑΜΚΑ 25088512345. "
            "Δικαιούχος: Καλλιόπη Στεφανάτου. Email: kstefanatou@webmail.gr."
        ),
        "spans": [
            {"label": "ama", "text": "8901234"},
            {"label": "amka", "text": "25088512345"},
            {"label": "private_person", "text": "Καλλιόπη Στεφανάτου"},
            {"label": "private_email", "text": "kstefanatou@webmail.gr"},
        ],
    },

    # --- Real Estate / Address heavy (93-98) ---
    {
        "id": 93,
        "register": "real_estate_listing",
        "text": (
            "Πωλείται διαμέρισμα 95τμ στη διεύθυνση Λεωφ. Συγγρού 138, 17671 Καλλιθέα. "
            "Επικοινωνία πωλητή: Νίκος Ζαχαριάς, τηλ. 6943217865."
        ),
        "spans": [
            {"label": "private_address", "text": "Λεωφ. Συγγρού 138, 17671 Καλλιθέα"},
            {"label": "private_person", "text": "Νίκος Ζαχαριάς"},
            {"label": "private_phone", "text": "6943217865"},
        ],
    },
    {
        "id": 94,
        "register": "rental_agreement",
        "text": (
            "Συμφωνητικό μίσθωσης κατοικίας. Εκμισθωτής: Ανδρέας Παππάς (ΑΦΜ 145678923). "
            "Μισθωτής: Ελένη Κωνσταντίνου. Ακίνητο: Σόλωνος 45, 10672 Αθήνα."
        ),
        "spans": [
            {"label": "private_person", "text": "Ανδρέας Παππάς"},
            {"label": "afm", "text": "145678923"},
            {"label": "private_person", "text": "Ελένη Κωνσταντίνου"},
            {"label": "private_address", "text": "Σόλωνος 45, 10672 Αθήνα"},
        ],
    },
    {
        "id": 95,
        "register": "address_change_notice",
        "text": (
            "Παρακαλώ αλλάξτε τη διεύθυνση επικοινωνίας από Πατησίων 123, Αθήνα σε "
            "Φιλελλήνων 7, 10557 Αθήνα. Δικαιούχος: Σπυρίδων Παναγιωτόπουλος, "
            "ΑΦΜ 234561789."
        ),
        "spans": [
            {"label": "private_address", "text": "Πατησίων 123, Αθήνα"},
            {"label": "private_address", "text": "Φιλελλήνων 7, 10557 Αθήνα"},
            {"label": "private_person", "text": "Σπυρίδων Παναγιωτόπουλος"},
            {"label": "afm", "text": "234561789"},
        ],
    },
    {
        "id": 96,
        "register": "property_tax_notice",
        "text": (
            "Φόρος ακίνητης περιουσίας 2026 για ακίνητο στη διεύθυνση Δοϊράνης 12, 17672 "
            "Καλλιθέα. Ιδιοκτήτης Στέφανος Καρρά, ΑΦΜ 198234561. Ποσό: 487€."
        ),
        "spans": [
            {"label": "private_address", "text": "Δοϊράνης 12, 17672 Καλλιθέα"},
            {"label": "private_person", "text": "Στέφανος Καρρά"},
            {"label": "afm", "text": "198234561"},
        ],
    },
    {
        "id": 97,
        "register": "moving_company_quote",
        "text": (
            "Προσφορά μετακόμισης από Λεωφ. Κηφισίας 89, Μαρούσι προς Νίκης 23, 10557 Αθήνα. "
            "Πελάτης: Φωτεινή Ζήση, fzisiq@email.gr, 6951234876."
        ),
        "spans": [
            {"label": "private_address", "text": "Λεωφ. Κηφισίας 89, Μαρούσι"},
            {"label": "private_address", "text": "Νίκης 23, 10557 Αθήνα"},
            {"label": "private_person", "text": "Φωτεινή Ζήση"},
            {"label": "private_email", "text": "fzisiq@email.gr"},
            {"label": "private_phone", "text": "6951234876"},
        ],
    },
    {
        "id": 98,
        "register": "delivery_address_form",
        "text": (
            "Στοιχεία παράδοσης: Ονοματεπώνυμο Παρασκευή Λάππα, οδός Σεβαστουπόλεως 33, "
            "11526 Αμπελόκηποι, τηλ 6932145987."
        ),
        "spans": [
            {"label": "private_person", "text": "Παρασκευή Λάππα"},
            {"label": "private_address", "text": "Σεβαστουπόλεως 33, 11526 Αμπελόκηποι"},
            {"label": "private_phone", "text": "6932145987"},
        ],
    },

    # --- Vehicle / Plate / VIN heavy (99-104) ---
    {
        "id": 99,
        "register": "rental_car_contract",
        "text": (
            "Ενοικίαση οχήματος. Πινακίδα: ΥΧΖ-7689. VIN: 1HGCM82633A123456. "
            "Ενοικιαστής: Παύλος Χριστοδούλου, διαβατήριο AΓ8765432, "
            "δίπλωμα οδήγησης 567823901."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΥΧΖ-7689"},
            {"label": "vehicle_vin", "text": "1HGCM82633A123456"},
            {"label": "private_person", "text": "Παύλος Χριστοδούλου"},
            {"label": "passport", "text": "AΓ8765432"},
            {"label": "driver_license", "text": "567823901"},
        ],
    },
    {
        "id": 100,
        "register": "police_chase_radio",
        "text": (
            "Εκπομπή ασύρματου: Όχημα ΖΕΖ-1457 διαφεύγει βορείως, οδηγός με ΑΔΤ ΞΛ-456789, "
            "δίπλωμα 234567109. Κατευθυνθείτε."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΖΕΖ-1457"},
            {"label": "adt", "text": "ΞΛ-456789"},
            {"label": "driver_license", "text": "234567109"},
        ],
    },
    {
        "id": 101,
        "register": "vehicle_import_form",
        "text": (
            "Δήλωση εισαγωγής οχήματος. Μάρκα: BMW. VIN: WBA7E2C56JG987654. "
            "Νέα πινακίδα: ΗΖΡ-3216. Κάτοχος: Νικολέτα Παπαδοπούλου."
        ),
        "spans": [
            {"label": "vehicle_vin", "text": "WBA7E2C56JG987654"},
            {"label": "license_plate", "text": "ΗΖΡ-3216"},
            {"label": "private_person", "text": "Νικολέτα Παπαδοπούλου"},
        ],
    },
    {
        "id": 102,
        "register": "lease_termination",
        "text": (
            "Λήξη μίσθωσης οχήματος Mercedes πιν. ΥΡΖ-4982, αρ. πλαισίου WDB2030461F123987. "
            "Επιστροφή: 30/06/2026."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΥΡΖ-4982"},
            {"label": "vehicle_vin", "text": "WDB2030461F123987"},
            {"label": "private_date", "text": "30/06/2026"},
        ],
    },
    {
        "id": 103,
        "register": "second_hand_motorbike",
        "text": (
            "Πωλείται μηχανή Yamaha XSR700, αρ. πλαισίου JYARN23E0KA012345, "
            "πινακίδα ΧΙΑ-2347. Τιμή: 4.500€. Επικοινωνία: stathis.bikes@gmail.com."
        ),
        "spans": [
            {"label": "vehicle_vin", "text": "JYARN23E0KA012345"},
            {"label": "license_plate", "text": "ΧΙΑ-2347"},
            {"label": "private_email", "text": "stathis.bikes@gmail.com"},
        ],
    },
    {
        "id": 104,
        "register": "driver_change_form",
        "text": (
            "Αλλαγή οδηγού στο όχημα ΖΕΥ-7821. Νέος οδηγός: Παναγιώτης Ζαχαρόπουλος, "
            "δίπλωμα οδήγησης 345781290, ισχύς από 12/04/2026."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΖΕΥ-7821"},
            {"label": "private_person", "text": "Παναγιώτης Ζαχαρόπουλος"},
            {"label": "driver_license", "text": "345781290"},
            {"label": "private_date", "text": "12/04/2026"},
        ],
    },

    # --- IP / URL heavy (105-110) ---
    {
        "id": 105,
        "register": "phishing_alert",
        "text": (
            "Ανιχνεύθηκε phishing site στο http://secure-bank-login.tk/index.php?id=4567 "
            "από IP 185.234.56.78. Ανέφερε στο abuse@cert.gr."
        ),
        "spans": [
            {"label": "private_url", "text": "http://secure-bank-login.tk/index.php?id=4567"},
            {"label": "ip_address", "text": "185.234.56.78"},
            {"label": "private_email", "text": "abuse@cert.gr"},
        ],
    },
    {
        "id": 106,
        "register": "developer_handoff",
        "text": (
            "Repo: https://github.com/greek-startup/api-service. "
            "Staging URL: https://staging.api.greek-startup.gr/v2/health. "
            "Άντρας του pipeline: nikos.dev@startup.gr."
        ),
        "spans": [
            {"label": "private_url", "text": "https://github.com/greek-startup/api-service"},
            {"label": "private_url", "text": "https://staging.api.greek-startup.gr/v2/health"},
            {"label": "private_email", "text": "nikos.dev@startup.gr"},
        ],
    },
    {
        "id": 107,
        "register": "ssh_dst_log",
        "text": (
            "SSH connection from 78.123.45.67 to bastion 10.0.0.5 on port 22. "
            "User: ops-greek-2026. Geolocation: Athens, GR."
        ),
        "spans": [
            {"label": "ip_address", "text": "78.123.45.67"},
            {"label": "ip_address", "text": "10.0.0.5"},
        ],
    },
    {
        "id": 108,
        "register": "internal_app_link_email",
        "text": (
            "Πρόσβαση στο νέο εσωτερικό dashboard: https://reports.intranet.firm.gr/q1-2026/dashboard. "
            "Login με admin@firm.gr."
        ),
        "spans": [
            {"label": "private_url", "text": "https://reports.intranet.firm.gr/q1-2026/dashboard"},
            {"label": "private_email", "text": "admin@firm.gr"},
        ],
    },
    {
        "id": 109,
        "register": "ddos_alert",
        "text": (
            "DDoS attack source IP 203.45.187.102 hitting target 192.168.1.50 with 50k req/s. "
            "Mitigation: rate-limit at edge."
        ),
        "spans": [
            {"label": "ip_address", "text": "203.45.187.102"},
            {"label": "ip_address", "text": "192.168.1.50"},
        ],
    },
    {
        "id": 110,
        "register": "api_doc_link",
        "text": (
            "API documentation hosted στο https://docs.platform-gr.com/api/v3/spec.json. "
            "Παρακαλώ ελέγξτε πριν deploy."
        ),
        "spans": [
            {"label": "private_url", "text": "https://docs.platform-gr.com/api/v3/spec.json"},
        ],
    },

    # --- IBAN / Account / MAC fillers (111-115) ---
    {
        "id": 111,
        "register": "vendor_payment",
        "text": (
            "Πληρωμή προμηθευτή. IBAN: GR2002601800000045671234567. "
            "Δικαιούχος: Maritime Logistics ΕΕ. ΓΕΜΗ: 245678100000."
        ),
        "spans": [
            {"label": "iban_gr", "text": "GR2002601800000045671234567"},
            {"label": "gemi", "text": "245678100000"},
        ],
    },
    {
        "id": 112,
        "register": "iban_correction",
        "text": (
            "Διόρθωση IBAN από GR1601101250000000012300695 (παλαιό) σε "
            "GR1601101250000000012300999 (νέο). Επικοινωνία: bank.support@nbg.gr."
        ),
        "spans": [
            {"label": "iban_gr", "text": "GR1601101250000000012300695"},
            {"label": "iban_gr", "text": "GR1601101250000000012300999"},
            {"label": "private_email", "text": "bank.support@nbg.gr"},
        ],
    },
    {
        "id": 113,
        "register": "savings_account",
        "text": (
            "Ταμιευτήριο: λογαριασμός 9456-78901-234. Κάτοχος: Αναστασία Καπετάνου. "
            "Υπόλοιπο 12.456,78€."
        ),
        "spans": [
            {"label": "account_number", "text": "9456-78901-234"},
            {"label": "private_person", "text": "Αναστασία Καπετάνου"},
        ],
    },
    {
        "id": 114,
        "register": "iot_device_register",
        "text": (
            "Νέα IoT συσκευή. MAC: B8:27:EB:01:23:45. Hostname: greek-sensor-001. "
            "IP: 192.168.50.10."
        ),
        "spans": [
            {"label": "mac_address", "text": "B8:27:EB:01:23:45"},
            {"label": "ip_address", "text": "192.168.50.10"},
        ],
    },
    {
        "id": 115,
        "register": "switch_config",
        "text": (
            "Switch port assignment: port 24 → MAC 00:50:56:AB:CD:EF, VLAN 100. "
            "Documentation https://wiki.netadmin.gr/switches."
        ),
        "spans": [
            {"label": "mac_address", "text": "00:50:56:AB:CD:EF"},
            {"label": "private_url", "text": "https://wiki.netadmin.gr/switches"},
        ],
    },

    # --- IMEI / DL fillers (116-120) ---
    {
        "id": 116,
        "register": "warranty_claim_form",
        "text": (
            "Αξίωση εγγύησης συσκευής. IMEI 358912345671234. Πελάτης: Γεωργία Παπαδά. "
            "Email gpapada@protonmail.com."
        ),
        "spans": [
            {"label": "imei", "text": "358912345671234"},
            {"label": "private_person", "text": "Γεωργία Παπαδά"},
            {"label": "private_email", "text": "gpapada@protonmail.com"},
        ],
    },
    {
        "id": 117,
        "register": "carrier_unlock",
        "text": (
            "Αίτηση unlock κινητού IMEI 350123456789012. Συσκευή: iPhone 14 Pro. "
            "Κάτοχος: Ηρώ Κωσταρίδη, τηλ. 6942345678."
        ),
        "spans": [
            {"label": "imei", "text": "350123456789012"},
            {"label": "private_person", "text": "Ηρώ Κωσταρίδη"},
            {"label": "private_phone", "text": "6942345678"},
        ],
    },
    {
        "id": 118,
        "register": "professional_dl_form",
        "text": (
            "Επαγγελματικό δίπλωμα οδήγησης κατηγορίας Γ' αρ. 678123459. "
            "Κάτοχος: Κωνσταντίνος Παπαδημόπουλος. ΑΦΜ: 234578901."
        ),
        "spans": [
            {"label": "driver_license", "text": "678123459"},
            {"label": "private_person", "text": "Κωνσταντίνος Παπαδημόπουλος"},
            {"label": "afm", "text": "234578901"},
        ],
    },
    {
        "id": 119,
        "register": "license_suspended",
        "text": (
            "Αναστολή διπλώματος οδήγησης 098712345 για τρίμηνο, "
            "λόγω παράβασης Κ.Ο.Κ. Επιστροφή 31/07/2026."
        ),
        "spans": [
            {"label": "driver_license", "text": "098712345"},
            {"label": "private_date", "text": "31/07/2026"},
        ],
    },
    {
        "id": 120,
        "register": "device_serial_inv",
        "text": (
            "Καταγραφή συσκευών IT. Laptop SN: DEV-90412. Phone IMEI: 351987654321098. "
            "Tablet IMEI: 354123456987012. Owner inventory@firm.gr."
        ),
        "spans": [
            {"label": "imei", "text": "351987654321098"},
            {"label": "imei", "text": "354123456987012"},
            {"label": "private_email", "text": "inventory@firm.gr"},
        ],
    },
]
