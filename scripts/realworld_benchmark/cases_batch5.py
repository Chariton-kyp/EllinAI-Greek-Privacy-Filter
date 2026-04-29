"""Real-world benchmark cases — Batch 5 (40 cases, total 200).

Focus: adversarial / decoy / boundary-stress / inflection diversity /
flowing prose with scattered PII / mixed scripts (Greek + Latin +
Greeklish) / additional pcn/mac/ama fillers.
"""
from __future__ import annotations

CASES = [
    # --- Adversarial / decoy (161-166) ---
    {
        "id": 161,
        "register": "decoy_pure_text",
        "text": (
            "Το βιβλίο που μου πρότεινες ήταν εξαιρετικό. Η συγγραφή είναι πλούσια και τα "
            "θέματα προσελκύουν τον αναγνώστη σε κάθε σελίδα. Σε ευχαριστώ θερμά."
        ),
        "spans": [],
    },
    {
        "id": 162,
        "register": "decoy_numeric_noise",
        "text": (
            "Η εκπαιδευτική ενότητα 4567 περιλαμβάνει 12 κεφάλαια συνολικά. "
            "Στόχος: 90% επιτυχία στις εξετάσεις του 2026."
        ),
        "spans": [],
    },
    {
        "id": 163,
        "register": "almost_iban_decoy",
        "text": (
            "Παραγγελία reference number GR12345 (όχι IBAN, εσωτερικός κωδικός 5-ψήφιος). "
            "Επικοινωνία στο orders@shop.gr."
        ),
        "spans": [
            {"label": "private_email", "text": "orders@shop.gr"},
        ],
    },
    {
        "id": 164,
        "register": "almost_phone_decoy",
        "text": (
            "Ο γιατρός είπε ότι ο όγκος μειώθηκε κατά 6932148765 micrograms — όχι, "
            "αυτό είναι λάθος, πρέπει να σημαίνει 693 micrograms. Sorry για τη σύγχυση."
        ),
        "spans": [
            {"label": "private_phone", "text": "6932148765"},
        ],
    },
    {
        "id": 165,
        "register": "almost_card_decoy",
        "text": (
            "Στο πρότζεκτ έχουμε ID #4716-9876-5432-O098 (γράμμα O, όχι κάρτα). "
            "Δες details στο jira.firm.gr."
        ),
        "spans": [],
    },
    {
        "id": 166,
        "register": "test_data_marker",
        "text": (
            "Test record: 'John Doe' (placeholder), εικονικός λογαριασμός 0000-00000-000. "
            "Δεν χρησιμοποιείται σε production."
        ),
        "spans": [],
    },

    # --- Long flowing prose with scattered PII (167-172) ---
    {
        "id": 167,
        "register": "prose_news_anon",
        "text": (
            "Η κα Ευτυχία Παπαδόπουλου, γνωστή δημοσιογράφος, ανακοίνωσε χθες, στις "
            "14 Απριλίου 2026, ότι αποχωρεί από τα ΜΜΕ. Δηλώθηκε στο Τμήμα ΑΦΜ 087654321 "
            "και κατοικεί στη Λεωφ. Συγγρού 156, Νέα Σμύρνη. Επικοινωνία μέσω αντιπροσώπου "
            "στο 2109876543 ή στο efty.papad@news-bureau.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Ευτυχία Παπαδόπουλου"},
            {"label": "private_date", "text": "14 Απριλίου 2026"},
            {"label": "afm", "text": "087654321"},
            {"label": "private_address", "text": "Λεωφ. Συγγρού 156, Νέα Σμύρνη"},
            {"label": "private_phone", "text": "2109876543"},
            {"label": "private_email", "text": "efty.papad@news-bureau.gr"},
        ],
    },
    {
        "id": 168,
        "register": "long_medical_history",
        "text": (
            "Ιατρικό ιστορικό ασθενούς. Όνομα: Σταύρος Καρρά (γενν. 12/05/1972, "
            "ΑΜΚΑ 12057245678). Δείκτες πίεσης φυσιολογικοί από τη συστηματική θεραπεία "
            "που ξεκίνησε τον Νοέμβριο 2025. Παράπλευρες παθήσεις: διαβήτης τύπου 2. "
            "Συντονιστής φροντίδας: Δρ. Ευαγγελία Παππά, evpap@iatriko.gr, 6987234561."
        ),
        "spans": [
            {"label": "private_person", "text": "Σταύρος Καρρά"},
            {"label": "private_date", "text": "12/05/1972"},
            {"label": "amka", "text": "12057245678"},
            {"label": "private_person", "text": "Ευαγγελία Παππά"},
            {"label": "private_email", "text": "evpap@iatriko.gr"},
            {"label": "private_phone", "text": "6987234561"},
        ],
    },
    {
        "id": 169,
        "register": "ceo_intro_email",
        "text": (
            "Από τον CEO της εταιρείας μας, του κυρίου Ιωάννη Σαμαρά. Επικοινωνία: "
            "i.samaras@enterprise.gr. Όλες οι ερωτήσεις στρατηγικής στέλνονται στον CFO "
            "Δημήτρη Κωνσταντινίδη (dim.kon@enterprise.gr). Επιπρόσθετα, πληροφορίες "
            "για επενδυτικές σχέσεις στο https://investors.enterprise.gr/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννη Σαμαρά"},
            {"label": "private_email", "text": "i.samaras@enterprise.gr"},
            {"label": "private_person", "text": "Δημήτρη Κωνσταντινίδη"},
            {"label": "private_email", "text": "dim.kon@enterprise.gr"},
            {"label": "private_url", "text": "https://investors.enterprise.gr/2026"},
        ],
    },
    {
        "id": 170,
        "register": "long_legal_paragraph",
        "text": (
            "Με την υπ' αριθ. 4567/2026 αγωγή, ο ενάγων Παύλος Ζαχαριάς (ΑΦΜ 198765431, "
            "ΑΔΤ ΑΗ-901234, διαμένων Ομονοίας 12, Αθήνα) ζητά αποζημίωση 25.000€ από "
            "την εναγομένη εταιρεία Strato Logistics ΕΕ (ΓΕΜΗ 178945600000) για "
            "παράβαση συμβατικής υποχρέωσης που έλαβε χώρα στις 15 Σεπτεμβρίου 2025."
        ),
        "spans": [
            {"label": "private_person", "text": "Παύλος Ζαχαριάς"},
            {"label": "afm", "text": "198765431"},
            {"label": "adt", "text": "ΑΗ-901234"},
            {"label": "private_address", "text": "Ομονοίας 12, Αθήνα"},
            {"label": "gemi", "text": "178945600000"},
            {"label": "private_date", "text": "15 Σεπτεμβρίου 2025"},
        ],
    },
    {
        "id": 171,
        "register": "ride_share_receipt",
        "text": (
            "Ευχαριστούμε για την επιλογή σας. Διαδρομή από Σύνταγμα προς αεροδρόμιο. "
            "Συνολικό κόστος 38€ χρεώθηκε στην κάρτα Mastercard 5188 9234 7765 1234. "
            "Επιβάτης: Μαρία Ιωαννίδου, mioannidou@webmail.gr. "
            "Πινακίδα οχήματος ΥΧΖ-1234, οδηγός Δημήτρης Παπάς."
        ),
        "spans": [
            {"label": "card_pan", "text": "5188 9234 7765 1234"},
            {"label": "private_person", "text": "Μαρία Ιωαννίδου"},
            {"label": "private_email", "text": "mioannidou@webmail.gr"},
            {"label": "license_plate", "text": "ΥΧΖ-1234"},
            {"label": "private_person", "text": "Δημήτρης Παπάς"},
        ],
    },
    {
        "id": 172,
        "register": "gdpr_data_request",
        "text": (
            "Σύμφωνα με τον GDPR, ζητώ πρόσβαση στα προσωπικά δεδομένα που τηρείτε για "
            "εμένα. Ονοματεπώνυμο: Ηλίας Νικολαΐδης. ΑΦΜ: 156782349. Email registration: "
            "ilias.n@protonmail.com. Διεύθυνση εγγραφής: Νηρηίδων 8, Νέα Ιωνία. "
            "Επιθυμώ απάντηση εντός 30 ημερών."
        ),
        "spans": [
            {"label": "private_person", "text": "Ηλίας Νικολαΐδης"},
            {"label": "afm", "text": "156782349"},
            {"label": "private_email", "text": "ilias.n@protonmail.com"},
            {"label": "private_address", "text": "Νηρηίδων 8, Νέα Ιωνία"},
        ],
    },

    # --- Inflection diversity (173-180) ---
    {
        "id": 173,
        "register": "vocative_letter",
        "text": (
            "Αξιότιμε κύριε Δημητρακάκη, σας ενημερώνουμε ότι ολοκληρώθηκε η αίτηση. "
            "ΑΦΜ ταυτοποίησης: 234578912."
        ),
        "spans": [
            {"label": "private_person", "text": "Δημητρακάκη"},
            {"label": "afm", "text": "234578912"},
        ],
    },
    {
        "id": 174,
        "register": "genitive_signed_off",
        "text": (
            "Με εντολή του διευθυντή, του κυρίου Σταύρου Παναγιώτου, εκδίδεται η παρούσα "
            "βεβαίωση. ΑΦΜ εταιρείας: 098765431."
        ),
        "spans": [
            {"label": "private_person", "text": "Σταύρου Παναγιώτου"},
            {"label": "afm", "text": "098765431"},
        ],
    },
    {
        "id": 175,
        "register": "dative_archaic",
        "text": (
            "Τη Νικολέτα Παπαδημητρίου επιδίδεται η παρούσα κλήση μάρτυρα. "
            "ΑΔΤ ΞΛ-456789. Δικάσιμος 22/06/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικολέτα Παπαδημητρίου"},
            {"label": "adt", "text": "ΞΛ-456789"},
            {"label": "private_date", "text": "22/06/2026"},
        ],
    },
    {
        "id": 176,
        "register": "first_name_only",
        "text": (
            "Γιάννη, στείλε μου το ΑΦΜ 156234897 σου άμεσα. Πάμε για τη φορολογική σήμερα. "
            "Φωτεινή"
        ),
        "spans": [
            {"label": "private_person", "text": "Γιάννη"},
            {"label": "afm", "text": "156234897"},
            {"label": "private_person", "text": "Φωτεινή"},
        ],
    },
    {
        "id": 177,
        "register": "compound_surname",
        "text": (
            "Η οικογένεια Παπαδόπουλος-Ιωάννου ζητά μετεγγραφή για την κόρη τους Ευτυχία "
            "από το 4ο στο 6ο Δημοτικό. ΑΜΚΑ 21086512345."
        ),
        "spans": [
            {"label": "private_person", "text": "Παπαδόπουλος-Ιωάννου"},
            {"label": "private_person", "text": "Ευτυχία"},
            {"label": "amka", "text": "21086512345"},
        ],
    },
    {
        "id": 178,
        "register": "title_with_name",
        "text": (
            "Ο Δρ. Ιωάννης Παππαδημητρίου ηγείται της ομάδας. Επικοινωνία: "
            "i.papadim@uni.gr. Γραφείο 312, ώρες 10-14."
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννης Παππαδημητρίου"},
            {"label": "private_email", "text": "i.papadim@uni.gr"},
        ],
    },
    {
        "id": 179,
        "register": "patronymic_form",
        "text": (
            "Φοιτητής: Ιωάννης Δημητρίου του Νικολάου. ΑΜΦ: 1067201234. "
            "ΑΜΚΑ: 03128556712."
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννης Δημητρίου"},
            {"label": "private_person", "text": "Νικολάου"},
            {"label": "amka", "text": "03128556712"},
        ],
    },
    {
        "id": 180,
        "register": "diminutive_name",
        "text": (
            "Ο Στρατούλης (αγαπητικό) Λαμπρόπουλος, τηλ. 6932148765, "
            "θα παραλάβει τα δέματα την Τετάρτη."
        ),
        "spans": [
            {"label": "private_person", "text": "Στρατούλης"},
            {"label": "private_person", "text": "Λαμπρόπουλος"},
            {"label": "private_phone", "text": "6932148765"},
        ],
    },

    # --- More pcn / mac / ama (181-190) ---
    {
        "id": 181,
        "register": "epaitisi_pcn",
        "text": (
            "Επαίτηση επιδομάτων ΟΠΕΚΑ. ΠΑΠ δικαιούχου: 156782349P77. ΑΜΑ: 6789012."
        ),
        "spans": [
            {"label": "pcn", "text": "156782349P77"},
            {"label": "ama", "text": "6789012"},
        ],
    },
    {
        "id": 182,
        "register": "egov_recovery",
        "text": (
            "Ανάκτηση κωδικών gov.gr. PCN: 234567891T34, αποστολή OTP στο τηλ. 6987234561."
        ),
        "spans": [
            {"label": "pcn", "text": "234567891T34"},
            {"label": "private_phone", "text": "6987234561"},
        ],
    },
    {
        "id": 183,
        "register": "audit_report_macs",
        "text": (
            "Audit συσκευών δικτύου: MAC AC:DE:48:00:11:22, MAC 12:34:56:78:9A:BC, "
            "MAC FE:ED:FA:CE:00:01. Σύνδεση στο https://nms.netadmin.gr/audit-2026."
        ),
        "spans": [
            {"label": "mac_address", "text": "AC:DE:48:00:11:22"},
            {"label": "mac_address", "text": "12:34:56:78:9A:BC"},
            {"label": "mac_address", "text": "FE:ED:FA:CE:00:01"},
            {"label": "private_url", "text": "https://nms.netadmin.gr/audit-2026"},
        ],
    },
    {
        "id": 184,
        "register": "ika_branch_letter",
        "text": (
            "Από: Παράρτημα ΙΚΑ Αθηνών. Σας ενημερώνουμε ότι ο νέος ΑΜΑ "
            "ασφαλισμένου είναι 4567890. Επικοινωνία: ika.athens@efka.gr."
        ),
        "spans": [
            {"label": "ama", "text": "4567890"},
            {"label": "private_email", "text": "ika.athens@efka.gr"},
        ],
    },
    {
        "id": 185,
        "register": "iot_telemetry",
        "text": (
            "Τηλεμετρία: συσκευή MAC 02:00:00:01:23:45 αναφέρει θερμοκρασία 23°C. "
            "Endpoint https://telemetry.iot-platform.gr/api/v2/data."
        ),
        "spans": [
            {"label": "mac_address", "text": "02:00:00:01:23:45"},
            {"label": "private_url", "text": "https://telemetry.iot-platform.gr/api/v2/data"},
        ],
    },
    {
        "id": 186,
        "register": "ergani_form",
        "text": (
            "Σύστημα ΕΡΓΑΝΗ — Δήλωση πρόσληψης. Εργαζόμενος: Στυλιανή Παππά. "
            "ΑΜΑ ΙΚΑ: 5678012. ΑΦΜ: 167823945. Έναρξη 15/05/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Στυλιανή Παππά"},
            {"label": "ama", "text": "5678012"},
            {"label": "afm", "text": "167823945"},
            {"label": "private_date", "text": "15/05/2026"},
        ],
    },
    {
        "id": 187,
        "register": "ip_dual_stack",
        "text": (
            "Πελάτης συνδέθηκε από IPv4 78.45.123.234 και IPv6 (παραλείπεται). "
            "User agent: Greek/Mobile."
        ),
        "spans": [
            {"label": "ip_address", "text": "78.45.123.234"},
        ],
    },
    {
        "id": 188,
        "register": "data_breach_notif",
        "text": (
            "Ειδοποίηση παραβίασης δεδομένων. Επηρεασθέντες χρήστες: 12.000. "
            "Τα στοιχεία σας: email kostas.papadopoulos@gmail.com, IP πρόσβασης 195.78.234.10. "
            "Ενημερωθείτε στο https://breach.firm.gr/incident-2026."
        ),
        "spans": [
            {"label": "private_email", "text": "kostas.papadopoulos@gmail.com"},
            {"label": "ip_address", "text": "195.78.234.10"},
            {"label": "private_url", "text": "https://breach.firm.gr/incident-2026"},
        ],
    },
    {
        "id": 189,
        "register": "kte_social_post",
        "text": (
            "Φίλοι, βρήκα κινητό με IMEI 354978123456789 στο μετρό! "
            "Αν είναι δικό σας, ping me στο messenger ή email lostandfound@athens.gr."
        ),
        "spans": [
            {"label": "imei", "text": "354978123456789"},
            {"label": "private_email", "text": "lostandfound@athens.gr"},
        ],
    },
    {
        "id": 190,
        "register": "vehicle_full_record",
        "text": (
            "Στοιχεία οχήματος: Πινακίδα ΖΗΡ-9876, VIN VF1RFB00264123987, "
            "Ιδιοκτήτης Δημήτρης Παπακωνσταντίνου, ΑΦΜ 198765432, "
            "Δίπλωμα οδήγησης 234567891."
        ),
        "spans": [
            {"label": "license_plate", "text": "ΖΗΡ-9876"},
            {"label": "vehicle_vin", "text": "VF1RFB00264123987"},
            {"label": "private_person", "text": "Δημήτρης Παπακωνσταντίνου"},
            {"label": "afm", "text": "198765432"},
            {"label": "driver_license", "text": "234567891"},
        ],
    },

    # --- Multi-script / Greeklish (191-200) ---
    {
        "id": 191,
        "register": "greeklish_chat",
        "text": (
            "Geia sou Maria! Mou esteilan to AFM 234567891 alla nomizo einai lathos. "
            "Tilefono 6932145987 an theleis."
        ),
        "spans": [
            {"label": "private_person", "text": "Maria"},
            {"label": "afm", "text": "234567891"},
            {"label": "private_phone", "text": "6932145987"},
        ],
    },
    {
        "id": 192,
        "register": "english_business_email",
        "text": (
            "Dear Mr. Papadopoulos, your invoice (AFM 156782349) has been processed. "
            "IBAN GR8002601500000067812345678 will be debited on 15/06/2026. "
            "Contact: accounts@firm.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Papadopoulos"},
            {"label": "afm", "text": "156782349"},
            {"label": "iban_gr", "text": "GR8002601500000067812345678"},
            {"label": "private_date", "text": "15/06/2026"},
            {"label": "private_email", "text": "accounts@firm.gr"},
        ],
    },
    {
        "id": 193,
        "register": "mixed_greek_english",
        "text": (
            "Pinakida YHE-2384, owner Γιώργος Παππάς, τηλ. 6987234561. "
            "License plate verified at checkpoint."
        ),
        "spans": [
            {"label": "license_plate", "text": "YHE-2384"},
            {"label": "private_person", "text": "Γιώργος Παππάς"},
            {"label": "private_phone", "text": "6987234561"},
        ],
    },
    {
        "id": 194,
        "register": "polytonic_address",
        "text": (
            "Πρὸς τὴν κυρίαν Παρασκευὴν Καραμπίνην, διαμένουσαν ἐπὶ τῆς ὁδοῦ "
            "Πανεπιστημίου 42, Ἀθῆναι. ΑΦΜ 187654321."
        ),
        "spans": [
            {"label": "private_person", "text": "Παρασκευὴν Καραμπίνην"},
            {"label": "private_address", "text": "Πανεπιστημίου 42, Ἀθῆναι"},
            {"label": "afm", "text": "187654321"},
        ],
    },
    {
        "id": 195,
        "register": "abbreviated_form",
        "text": (
            "Στ. Παπαδόπ., ΑΦΜ 087654321, ΑΜΚΑ 12087245678, τηλ.: 6912345678, "
            "διεύθ.: Σολωμού 14, Αθ."
        ),
        "spans": [
            {"label": "private_person", "text": "Στ. Παπαδόπ."},
            {"label": "afm", "text": "087654321"},
            {"label": "amka", "text": "12087245678"},
            {"label": "private_phone", "text": "6912345678"},
            {"label": "private_address", "text": "Σολωμού 14, Αθ."},
        ],
    },
    {
        "id": 196,
        "register": "telegram_message",
        "text": (
            "Ορίστε τα στοιχεία:\n"
            "📧 papas2026@gmail.com\n"
            "📞 6987654321\n"
            "🏠 Πατησίων 89, Αθήνα\n"
            "💳 4716 9876 5432 1098\n"
            "Ευχαριστώ!"
        ),
        "spans": [
            {"label": "private_email", "text": "papas2026@gmail.com"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_address", "text": "Πατησίων 89, Αθήνα"},
            {"label": "card_pan", "text": "4716 9876 5432 1098"},
        ],
    },
    {
        "id": 197,
        "register": "form_field_dense",
        "text": (
            "Last Name: Karras\nFirst Name: Νικόλαος\nDOB: 14/05/1985\n"
            "Phone: 6932148765\nEmail: nkar@webmail.gr\nAFM: 234561987"
        ),
        "spans": [
            {"label": "private_person", "text": "Karras"},
            {"label": "private_person", "text": "Νικόλαος"},
            {"label": "private_date", "text": "14/05/1985"},
            {"label": "private_phone", "text": "6932148765"},
            {"label": "private_email", "text": "nkar@webmail.gr"},
            {"label": "afm", "text": "234561987"},
        ],
    },
    {
        "id": 198,
        "register": "international_invoice",
        "text": (
            "Invoice from German supplier. Buyer: Παπαδόπουλος ΕΕ, ΓΕΜΗ 145678300000, "
            "ΑΦΜ EL098765432. Wire to IBAN DE89370400440532013000 (German). "
            "Confirm at finance@papadopoulos.gr."
        ),
        "spans": [
            {"label": "gemi", "text": "145678300000"},
            {"label": "afm", "text": "098765432"},
            {"label": "private_email", "text": "finance@papadopoulos.gr"},
        ],
    },
    {
        "id": 199,
        "register": "twitter_complaint",
        "text": (
            "@CompanyGR εδώ και 3 μέρες δεν έχω απάντηση! Τηλ μου 6987234561, "
            "ticket #45678. Θα κάνω αναφορά στην ΑΠΔΠΧ αν δεν μου απαντήσετε."
        ),
        "spans": [
            {"label": "private_phone", "text": "6987234561"},
        ],
    },
    {
        "id": 200,
        "register": "linkedin_signature",
        "text": (
            "---\n"
            "Δημήτρης Καραντώνης | Senior Engineer\n"
            "📱 +30 6943217865\n"
            "💼 dim.kar@startup.gr\n"
            "🌐 https://www.linkedin.com/in/dim-karantonis-2026\n"
            "🏢 Λεωφ. Συγγρού 87, 11743 Αθήνα"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτρης Καραντώνης"},
            {"label": "private_phone", "text": "+30 6943217865"},
            {"label": "private_email", "text": "dim.kar@startup.gr"},
            {"label": "private_url", "text": "https://www.linkedin.com/in/dim-karantonis-2026"},
            {"label": "private_address", "text": "Λεωφ. Συγγρού 87, 11743 Αθήνα"},
        ],
    },
]
