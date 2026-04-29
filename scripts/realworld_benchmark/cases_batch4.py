"""Real-world benchmark cases — Batch 4 (40 cases).

Final fillers + register diversity. Adds: legal contracts, customer
support, education, social media/SMS informal, multi-class hard cases,
government letters, polytonic accents, Greeklish mix.
"""
from __future__ import annotations

CASES = [
    # --- Customer Support / Email Support (121-126) ---
    {
        "id": 121,
        "register": "support_ticket_open",
        "text": (
            "Καλημέρα, αντιμετωπίζω πρόβλημα με τον λογαριασμό μου 6789-12345-678. "
            "Έχω χρεωθεί δύο φορές το ίδιο ποσό. Στοιχεία: Νικόλαος Παπαθανασίου, "
            "ΑΦΜ 187654321, τηλ. 6912345670."
        ),
        "spans": [
            {"label": "account_number", "text": "6789-12345-678"},
            {"label": "private_person", "text": "Νικόλαος Παπαθανασίου"},
            {"label": "afm", "text": "187654321"},
            {"label": "private_phone", "text": "6912345670"},
        ],
    },
    {
        "id": 122,
        "register": "delivery_complaint",
        "text": (
            "Δεν παρέλαβα την παραγγελία #2026-08456. Διεύθυνση παράδοσης: "
            "Κρήτης 14, 11364 Αθήνα. Επικοινωνήστε ασαπ στο 6971234567."
        ),
        "spans": [
            {"label": "private_address", "text": "Κρήτης 14, 11364 Αθήνα"},
            {"label": "private_phone", "text": "6971234567"},
        ],
    },
    {
        "id": 123,
        "register": "subscription_cancel",
        "text": (
            "Παρακαλώ ακυρώστε τη συνδρομή μου. Email: maria.papadopoulou@yahoo.com. "
            "Κάρτα χρέωσης 4716 9876 5432 1098."
        ),
        "spans": [
            {"label": "private_email", "text": "maria.papadopoulou@yahoo.com"},
            {"label": "card_pan", "text": "4716 9876 5432 1098"},
        ],
    },
    {
        "id": 124,
        "register": "shipping_label",
        "text": (
            "Παραλήπτης: Ευστράτιος Νικολόπουλος\n"
            "Διεύθυνση: Αχιλλέως 56, 17567 Π. Φάληρο\n"
            "Τηλ: 6932109876\n"
            "Tracking: https://courier.gr/track/AB123456789GR"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευστράτιος Νικολόπουλος"},
            {"label": "private_address", "text": "Αχιλλέως 56, 17567 Π. Φάληρο"},
            {"label": "private_phone", "text": "6932109876"},
            {"label": "private_url", "text": "https://courier.gr/track/AB123456789GR"},
        ],
    },
    {
        "id": 125,
        "register": "warranty_lookup",
        "text": (
            "Αναζήτηση εγγύησης. Στοιχεία: Σταυρούλα Νικολαΐδου, "
            "snikolaidou@webmail.gr, IMEI συσκευής 359123456712345."
        ),
        "spans": [
            {"label": "private_person", "text": "Σταυρούλα Νικολαΐδου"},
            {"label": "private_email", "text": "snikolaidou@webmail.gr"},
            {"label": "imei", "text": "359123456712345"},
        ],
    },
    {
        "id": 126,
        "register": "ecommerce_password_reset",
        "text": (
            "Επαναφορά κωδικού. Email: kostas.dim@protonmail.gr. "
            "Σύνδεσμος https://shop.greek.gr/reset/abc123xyz789."
        ),
        "spans": [
            {"label": "private_email", "text": "kostas.dim@protonmail.gr"},
            {"label": "private_url", "text": "https://shop.greek.gr/reset/abc123xyz789"},
        ],
    },

    # --- Legal contracts / Court (127-132) ---
    {
        "id": 127,
        "register": "lawsuit_filing",
        "text": (
            "Αγωγή ενώπιον Ειρηνοδικείου Αθηνών. Ενάγων: Παρασκευή Σπυριδάκη "
            "(ΑΦΜ 234561789, ΑΔΤ ΒΗ-456712). Εναγόμενος: Σύμβολο ΑΕ (ΓΕΜΗ 178945612000)."
        ),
        "spans": [
            {"label": "private_person", "text": "Παρασκευή Σπυριδάκη"},
            {"label": "afm", "text": "234561789"},
            {"label": "adt", "text": "ΒΗ-456712"},
            {"label": "gemi", "text": "178945612000"},
        ],
    },
    {
        "id": 128,
        "register": "power_of_attorney",
        "text": (
            "Πληρεξούσιο. Πληρεξουσιοδότης: Ιωάννης Παπαδημητρίου, ΑΔΤ ΖΞ-345678, "
            "ΑΦΜ 098765431. Πληρεξούσιος: Ευαγγελία Νικολάου, ΑΔΤ ΑΘ-901234."
        ),
        "spans": [
            {"label": "private_person", "text": "Ιωάννης Παπαδημητρίου"},
            {"label": "adt", "text": "ΖΞ-345678"},
            {"label": "afm", "text": "098765431"},
            {"label": "private_person", "text": "Ευαγγελία Νικολάου"},
            {"label": "adt", "text": "ΑΘ-901234"},
        ],
    },
    {
        "id": 129,
        "register": "will_testament",
        "text": (
            "Διαθήκη. Διαθέτης: Στυλιανός Κατσούλης, γενν. 14 Νοεμβρίου 1945, "
            "ΑΦΜ 187654321, κάτοικος οδού Ιπποκράτους 23, Αθήνα."
        ),
        "spans": [
            {"label": "private_person", "text": "Στυλιανός Κατσούλης"},
            {"label": "private_date", "text": "14 Νοεμβρίου 1945"},
            {"label": "afm", "text": "187654321"},
            {"label": "private_address", "text": "Ιπποκράτους 23, Αθήνα"},
        ],
    },
    {
        "id": 130,
        "register": "court_decision_pdf",
        "text": (
            "Απόφαση 4567/2026 Πολυμελούς Πρωτοδικείου. Ενάγων Δημήτριος Ζαχαρίας vs. "
            "Mediterranean Trade ΕΕ (ΓΕΜΗ 089453200000). Δικάσιμος 12/05/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτριος Ζαχαρίας"},
            {"label": "gemi", "text": "089453200000"},
            {"label": "private_date", "text": "12/05/2026"},
        ],
    },
    {
        "id": 131,
        "register": "settlement_agreement",
        "text": (
            "Συμβιβασμός. Ποσό αποζημίωσης 15.000€ προς τον Ηρακλή Παππά "
            "(ΑΦΜ 165432897, IBAN GR3201101900190200012345678)."
        ),
        "spans": [
            {"label": "private_person", "text": "Ηρακλή Παππά"},
            {"label": "afm", "text": "165432897"},
            {"label": "iban_gr", "text": "GR3201101900190200012345678"},
        ],
    },
    {
        "id": 132,
        "register": "criminal_complaint",
        "text": (
            "Μηνυτήρια αναφορά. Μηνυτής: Άννα Παπαδάκη, διεύθυνση Λεωφ. Αλεξάνδρας 78, "
            "Αθήνα. ΑΔΤ ΗΗ-678123. Επικοινωνία 6987234561."
        ),
        "spans": [
            {"label": "private_person", "text": "Άννα Παπαδάκη"},
            {"label": "private_address", "text": "Λεωφ. Αλεξάνδρας 78, Αθήνα"},
            {"label": "adt", "text": "ΗΗ-678123"},
            {"label": "private_phone", "text": "6987234561"},
        ],
    },

    # --- Education (133-138) ---
    {
        "id": 133,
        "register": "university_enrollment",
        "text": (
            "Εγγραφή στο ΕΚΠΑ. Φοιτητής: Πέτρος Καραβίτης. ΑΜ φοιτητή: 1067201600. "
            "ΑΦΜ: 165432198. Διεύθυνση: Σολωμού 87, Αθήνα. Email: pkaravitis@uoa.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Πέτρος Καραβίτης"},
            {"label": "afm", "text": "165432198"},
            {"label": "private_address", "text": "Σολωμού 87, Αθήνα"},
            {"label": "private_email", "text": "pkaravitis@uoa.gr"},
        ],
    },
    {
        "id": 134,
        "register": "school_certificate",
        "text": (
            "Πιστοποιητικό σπουδών για τον μαθητή Νικόλαο Παππά, "
            "ΑΜΚΑ 25088923456, σχολικό έτος 2025-2026, Α' Λυκείου."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλαο Παππά"},
            {"label": "amka", "text": "25088923456"},
        ],
    },
    {
        "id": 135,
        "register": "scholarship_letter",
        "text": (
            "Χορήγηση υποτροφίας ΙΚΥ. Δικαιούχος: Ελευθερία Παπαθανασίου. "
            "ΑΦΜ 198432567. ΑΜΚΑ 16018045678. Καταβολή στον IBAN GR2401407901230012345678901."
        ),
        "spans": [
            {"label": "private_person", "text": "Ελευθερία Παπαθανασίου"},
            {"label": "afm", "text": "198432567"},
            {"label": "amka", "text": "16018045678"},
            {"label": "iban_gr", "text": "GR2401407901230012345678901"},
        ],
    },
    {
        "id": 136,
        "register": "teacher_assignment",
        "text": (
            "Διορισμός εκπαιδευτικού. Όνομα: Δημητριάνα Σταματάκη, "
            "ΑΜ ΑΣΕΠ 567824. Σχολείο: 8ο Γυμνάσιο Αθηνών. Έναρξη 01/09/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Δημητριάνα Σταματάκη"},
            {"label": "private_date", "text": "01/09/2026"},
        ],
    },
    {
        "id": 137,
        "register": "student_loan_application",
        "text": (
            "Δανειοδότηση φοιτητή. Αιτών: Παύλος Χριστοδουλόπουλος, "
            "ΑΦΜ 198765431, IBAN GR1402601200000067812345678. Email pavlos.cd@gmail.com."
        ),
        "spans": [
            {"label": "private_person", "text": "Παύλος Χριστοδουλόπουλος"},
            {"label": "afm", "text": "198765431"},
            {"label": "iban_gr", "text": "GR1402601200000067812345678"},
            {"label": "private_email", "text": "pavlos.cd@gmail.com"},
        ],
    },
    {
        "id": 138,
        "register": "thesis_supervisor",
        "text": (
            "Ανάθεση διπλωματικής. Φοιτητής Άρης Γαρδικιώτης. Επιβλέπων: "
            "Καθηγητής Δρ. Σπύρος Καρδαμίτσης. Email: sk@cs.uoa.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Άρης Γαρδικιώτης"},
            {"label": "private_person", "text": "Σπύρος Καρδαμίτσης"},
            {"label": "private_email", "text": "sk@cs.uoa.gr"},
        ],
    },

    # --- Multi-class hard cases / Greeklish mix (139-144) ---
    {
        "id": 139,
        "register": "informal_sms_chat",
        "text": (
            "Γεια Δημήτρη! Χρειάζομαι το AFM σου 156234897 και AMKA 14098056712 "
            "για τη συνταγή. Επίσης το tilefono 6932148765. Ευχαριστώ!"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημήτρη"},
            {"label": "afm", "text": "156234897"},
            {"label": "amka", "text": "14098056712"},
            {"label": "private_phone", "text": "6932148765"},
        ],
    },
    {
        "id": 140,
        "register": "polytonic_legal",
        "text": (
            "Πρὸς τὸν κύριον Νικόλαον Παπαδόπουλον, ἀριθ. φορολογ. μητρώου 124567891, "
            "ταυτοτ. ΞΖ-456712, διαμένοντα ἐπὶ τῆς ὁδοῦ Ἀκαδημίας 23."
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλαον Παπαδόπουλον"},
            {"label": "afm", "text": "124567891"},
            {"label": "adt", "text": "ΞΖ-456712"},
            {"label": "private_address", "text": "Ἀκαδημίας 23"},
        ],
    },
    {
        "id": 141,
        "register": "multi_pii_form",
        "text": (
            "Στοιχεία αίτησης: Ονομ. Παπαδόπουλος Νικόλαος | ΑΦΜ 087654321 | "
            "ΑΜΚΑ 03127895432 | ΑΔΤ ΑΖ-345678 | ΓΕΜΗ εταιρείας 245678300000 | "
            "Διπλ. οδήγησης 234578102 | IBAN GR1606601200004567812345678 | "
            "Τηλ. 2103456789 | Email npapadopoulos@firm.gr | "
            "Διεύθ. Κηφισίας 24, 11526 Αθήνα."
        ),
        "spans": [
            {"label": "private_person", "text": "Παπαδόπουλος Νικόλαος"},
            {"label": "afm", "text": "087654321"},
            {"label": "amka", "text": "03127895432"},
            {"label": "adt", "text": "ΑΖ-345678"},
            {"label": "gemi", "text": "245678300000"},
            {"label": "driver_license", "text": "234578102"},
            {"label": "iban_gr", "text": "GR1606601200004567812345678"},
            {"label": "private_phone", "text": "2103456789"},
            {"label": "private_email", "text": "npapadopoulos@firm.gr"},
            {"label": "private_address", "text": "Κηφισίας 24, 11526 Αθήνα"},
        ],
    },
    {
        "id": 142,
        "register": "informal_email",
        "text": (
            "Γιάννη μου, στείλε το νέο imei 359123456789012 και πινακίδα ΥΞΗ-3456 "
            "για το συμβόλαιο. Στο papas@yahoo.gr ok? Παύλος."
        ),
        "spans": [
            {"label": "private_person", "text": "Γιάννη"},
            {"label": "imei", "text": "359123456789012"},
            {"label": "license_plate", "text": "ΥΞΗ-3456"},
            {"label": "private_email", "text": "papas@yahoo.gr"},
            {"label": "private_person", "text": "Παύλος"},
        ],
    },
    {
        "id": 143,
        "register": "vocative_address",
        "text": (
            "Αγαπητέ κ. Παπαδόπουλε, η αίτησή σας με ΑΦΜ 234561897 παρελήφθη. "
            "Παρακαλούμε πιστοποιήστε ταυτότητα ΑΔΤ ΗΘ-456712 πριν την Παρασκευή 15 Μαΐου 2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Παπαδόπουλε"},
            {"label": "afm", "text": "234561897"},
            {"label": "adt", "text": "ΗΘ-456712"},
            {"label": "private_date", "text": "15 Μαΐου 2026"},
        ],
    },
    {
        "id": 144,
        "register": "genitive_address",
        "text": (
            "Παραλήπτης: Της κυρίας Ευαγγελίας Παπαδημητρίου, ΑΦΜ 089654321, "
            "διεύθυνση Νικαίας 14, Πειραιάς. Συστημένο νο 4567/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Ευαγγελίας Παπαδημητρίου"},
            {"label": "afm", "text": "089654321"},
            {"label": "private_address", "text": "Νικαίας 14, Πειραιάς"},
        ],
    },

    # --- Government / Letters (145-150) ---
    {
        "id": 145,
        "register": "registry_birth_certificate",
        "text": (
            "Πιστοποιητικό γέννησης. Όνομα: Ηλιάνα Καρρά. Ημ. γέννησης: 03 Μαρτίου 2010. "
            "Διεύθυνση: Νάξου 12, Αθήνα. ΑΜΚΑ: 03031045678."
        ),
        "spans": [
            {"label": "private_person", "text": "Ηλιάνα Καρρά"},
            {"label": "private_date", "text": "03 Μαρτίου 2010"},
            {"label": "private_address", "text": "Νάξου 12, Αθήνα"},
            {"label": "amka", "text": "03031045678"},
        ],
    },
    {
        "id": 146,
        "register": "marriage_certificate",
        "text": (
            "Πιστοποιητικό γάμου ΛΗΞ-2026/4567. Σύζυγοι: Παύλος Νικολαΐδης (ΑΦΜ 145673289) "
            "και Άννα Παππά (ΑΔΤ ΖΞ-789012). Ημ. τέλεσης 14 Φεβρουαρίου 2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Παύλος Νικολαΐδης"},
            {"label": "afm", "text": "145673289"},
            {"label": "private_person", "text": "Άννα Παππά"},
            {"label": "adt", "text": "ΖΞ-789012"},
            {"label": "private_date", "text": "14 Φεβρουαρίου 2026"},
        ],
    },
    {
        "id": 147,
        "register": "kep_appointment",
        "text": (
            "Ραντεβού στο ΚΕΠ Νέας Σμύρνης για ΑΜΚΑ 27065834567. "
            "Πολίτης: Μάριος Ζαχαριάδης. Ώρα 10:30, ημ. 22 Απριλίου 2026."
        ),
        "spans": [
            {"label": "amka", "text": "27065834567"},
            {"label": "private_person", "text": "Μάριος Ζαχαριάδης"},
            {"label": "private_date", "text": "22 Απριλίου 2026"},
        ],
    },
    {
        "id": 148,
        "register": "passport_office_letter",
        "text": (
            "Από τη Διεύθυνση Διαβατηρίων Αθηνών προς τον κο Σταύρο Δημητρίου. "
            "Διαβατήριο AΦ-3456789 έτοιμο για παραλαβή. Παρουσιαστείτε με ΑΔΤ ΑΞ-678123."
        ),
        "spans": [
            {"label": "private_person", "text": "Σταύρο Δημητρίου"},
            {"label": "passport", "text": "AΦ-3456789"},
            {"label": "adt", "text": "ΑΞ-678123"},
        ],
    },
    {
        "id": 149,
        "register": "voter_registration",
        "text": (
            "Εγγραφή στους εκλογικούς καταλόγους. Στοιχεία: Παρασκευή Νικολάου, "
            "ΑΔΤ ΞΞ-456789, διεύθυνση Σταδίου 34, Αθήνα. Δήμος Αθηναίων."
        ),
        "spans": [
            {"label": "private_person", "text": "Παρασκευή Νικολάου"},
            {"label": "adt", "text": "ΞΞ-456789"},
            {"label": "private_address", "text": "Σταδίου 34, Αθήνα"},
        ],
    },
    {
        "id": 150,
        "register": "child_benefit_form",
        "text": (
            "Επίδομα τέκνου ΟΠΕΚΑ. Δικαιούχος: Νεκταρία Παπαδημόπουλου. "
            "ΑΜΚΑ 18098234567. Τέκνα: 2. IBAN GR0902601500000067812345987."
        ),
        "spans": [
            {"label": "private_person", "text": "Νεκταρία Παπαδημόπουλου"},
            {"label": "amka", "text": "18098234567"},
            {"label": "iban_gr", "text": "GR0902601500000067812345987"},
        ],
    },

    # --- Edge / boundary cases (151-160) ---
    {
        "id": 151,
        "register": "url_with_query_params",
        "text": (
            "Παρακαλώ επισκεφθείτε τον σύνδεσμο https://app.tax.gov.gr/portal?afm=234567891&token=abc "
            "για ολοκλήρωση. Ισχύει έως 30/04/2026."
        ),
        "spans": [
            {"label": "private_url", "text": "https://app.tax.gov.gr/portal?afm=234567891&token=abc"},
            {"label": "private_date", "text": "30/04/2026"},
        ],
    },
    {
        "id": 152,
        "register": "long_secret_kv",
        "text": (
            "ENV variables: SECRET_KEY=django-insecure-h3ll0w0rldGr33kUB3rS3cr3t1234567890abcdefXY, "
            "DATABASE_URL=postgres://user:pass@localhost/db. Source: ops@firm.gr."
        ),
        "spans": [
            {"label": "secret", "text": "django-insecure-h3ll0w0rldGr33kUB3rS3cr3t1234567890abcdefXY"},
            {"label": "private_email", "text": "ops@firm.gr"},
        ],
    },
    {
        "id": 153,
        "register": "iban_dense_field",
        "text": (
            "Form: Όνομα=Παπαδόπουλος|ΑΦΜ=156234789|IBAN=GR8002601500000067812345678|τηλ=6987234561"
        ),
        "spans": [
            {"label": "private_person", "text": "Παπαδόπουλος"},
            {"label": "afm", "text": "156234789"},
            {"label": "iban_gr", "text": "GR8002601500000067812345678"},
            {"label": "private_phone", "text": "6987234561"},
        ],
    },
    {
        "id": 154,
        "register": "phone_intl_format",
        "text": (
            "Επικοινωνία: +30 210 3456789 (γραφείο) ή +30 6932148765 (κινητό). "
            "Email: support@hellenic-co.gr."
        ),
        "spans": [
            {"label": "private_phone", "text": "+30 210 3456789"},
            {"label": "private_phone", "text": "+30 6932148765"},
            {"label": "private_email", "text": "support@hellenic-co.gr"},
        ],
    },
    {
        "id": 155,
        "register": "name_with_accent_variant",
        "text": (
            "Συντονιστής έργου: Γιωργος Παπασταυρου (μονοτονικά). Email: gpapastavrou@uni.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Γιωργος Παπασταυρου"},
            {"label": "private_email", "text": "gpapastavrou@uni.gr"},
        ],
    },
    {
        "id": 156,
        "register": "card_no_spaces",
        "text": (
            "Αρ. κάρτας 4716987654321098 με CVV 472. Κάτοχος Σπύρος Λαζαρίδης."
        ),
        "spans": [
            {"label": "card_pan", "text": "4716987654321098"},
            {"label": "cvv", "text": "472"},
            {"label": "private_person", "text": "Σπύρος Λαζαρίδης"},
        ],
    },
    {
        "id": 157,
        "register": "ipv4_in_brackets",
        "text": (
            "Server logs δείχνουν είσοδο από [78.45.123.180] στις 14:32. "
            "Μπλοκάρισμα σε firewall.policy@netadmin.gr."
        ),
        "spans": [
            {"label": "ip_address", "text": "78.45.123.180"},
            {"label": "private_email", "text": "firewall.policy@netadmin.gr"},
        ],
    },
    {
        "id": 158,
        "register": "no_pii_decoy",
        "text": (
            "Ευχαριστώ πολύ για την εξυπηρέτηση. Όλα είναι εντάξει και θα επικοινωνήσω εγώ "
            "αν χρειαστεί κάτι."
        ),
        "spans": [],
    },
    {
        "id": 159,
        "register": "almost_pan_decoy",
        "text": (
            "Παραγγελία αρ. 4716-1234-5678-O123 (όχι αριθμός κάρτας, internal ref). "
            "Επεξεργαστής orders@shop.gr."
        ),
        "spans": [
            {"label": "private_email", "text": "orders@shop.gr"},
        ],
    },
    {
        "id": 160,
        "register": "phone_in_paragraph",
        "text": (
            "Ο νέος γιατρός συνεργάτης Κωνσταντίνος Μαυρομάτης διατηρεί ιατρείο επί της "
            "οδού Σκουφά 65. Για ραντεβού καλέστε στο 2103267890 ή στείλτε email στο "
            "kmavromatis@iatreion.gr."
        ),
        "spans": [
            {"label": "private_person", "text": "Κωνσταντίνος Μαυρομάτης"},
            {"label": "private_address", "text": "Σκουφά 65"},
            {"label": "private_phone", "text": "2103267890"},
            {"label": "private_email", "text": "kmavromatis@iatreion.gr"},
        ],
    },
]
