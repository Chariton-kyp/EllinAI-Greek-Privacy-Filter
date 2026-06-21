"""Greek PII Public Benchmark v1 — Part 4 (cases 76-100).

Vehicle continued (76-80), Education (81-90), Informal/SMS (91-100).

All values synthetic. License: CC-BY-4.0.
"""
from __future__ import annotations

CASES = [
    # ============== VEHICLE continued (76-80) ==============
    {
        "id": 76,
        "register": "car_rental_contract",
        "text": (
            "Hertz Hellas — Συμβόλαιο Ενοικίασης\n"
            "Πελάτης: Νικόλαος Ευθυμίου\n"
            "Δίπλωμα οδήγησης 156782349\n"
            "ΑΔΤ: ΑΡ-345891 | Διαβατήριο: ΑΟ4567823\n"
            "Όχημα: Fiat 500, ΥΑΘ-3470\n"
            "VIN: ZFA31200000123456\n"
            "Ημ.ενοικίασης: 14/05/2026 - 18/05/2026\n"
            "Πληρωμή: 4567 8901 2345 6789 (CVV 893)\n"
            "Email: nikos.eft@example.gr | Τηλ: 6987234567"
        ),
        "spans": [
            {"label": "private_person", "text": "Νικόλαος Ευθυμίου"},
            {"label": "driver_license", "text": "156782349"},
            {"label": "adt", "text": "ΑΡ-345891"},
            {"label": "passport", "text": "ΑΟ4567823"},
            {"label": "license_plate", "text": "ΥΑΘ-3470"},
            {"label": "vehicle_vin", "text": "ZFA31200000123456"},
            {"label": "private_date", "text": "14/05/2026"},
            {"label": "private_date", "text": "18/05/2026"},
            {"label": "card_pan", "text": "4567 8901 2345 6789"},
            {"label": "cvv", "text": "893"},
            {"label": "private_email", "text": "nikos.eft@example.gr"},
            {"label": "private_phone", "text": "6987234567"},
        ],
    },
    {
        "id": 77,
        "register": "vehicle_transfer",
        "text": (
            "Μεταβίβαση Αυτοκινήτου — Συμβόλαιο\n"
            "Πωλητής: Παύλος Δράκος, ΑΦΜ 817886323, ΑΔΤ ΑΖ-890123\n"
            "Αγοραστής: Σοφία Καραντινού, ΑΦΜ 795513786, ΑΔΤ ΑΗ-345671\n"
            "Όχημα: Volkswagen Golf, ΡΥΕ-2345, VIN WVWZZZ1JZXW123456\n"
            "Τιμή: 8.500€ | Ημ. μεταβίβασης: 25/04/2026\n"
            "Email πωλητή: paulos.d@example.gr"
        ),
        "spans": [
            {"label": "private_person", "text": "Παύλος Δράκος"},
            {"label": "afm", "text": "817886323"},
            {"label": "adt", "text": "ΑΖ-890123"},
            {"label": "private_person", "text": "Σοφία Καραντινού"},
            {"label": "afm", "text": "795513786"},
            {"label": "adt", "text": "ΑΗ-345671"},
            {"label": "license_plate", "text": "ΡΥΕ-2345"},
            {"label": "vehicle_vin", "text": "WVWZZZ1JZXW123456"},
            {"label": "private_date", "text": "25/04/2026"},
            {"label": "private_email", "text": "paulos.d@example.gr"},
        ],
    },
    {
        "id": 78,
        "register": "uber_driver_signup",
        "text": (
            "Uber Driver — Εγγραφή\n"
            "Όνομα: Μάνος Παπαδημητρίου\n"
            "ΑΦΜ: 156782349 | Διπλ. οδήγησης 441314247\n"
            "Όχημα: Skoda Octavia, ΚΗΞ-4567, VIN TMBJK21Z1B1234567\n"
            "Email: manos.uber@example.com\n"
            "Κιν.: 6932456789\n"
            "IBAN πληρωμών: GR36 4790 9972 8289 6793 2828 651\n"
            "Έναρξη: 18/05/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Μάνος Παπαδημητρίου"},
            {"label": "afm", "text": "156782349"},
            {"label": "driver_license", "text": "441314247"},
            {"label": "license_plate", "text": "ΚΗΞ-4567"},
            {"label": "vehicle_vin", "text": "TMBJK21Z1B1234567"},
            {"label": "private_email", "text": "manos.uber@example.com"},
            {"label": "private_phone", "text": "6932456789"},
            {"label": "iban_gr", "text": "GR36 4790 9972 8289 6793 2828 651"},
            {"label": "private_date", "text": "18/05/2026"},
        ],
    },
    {
        "id": 79,
        "register": "vehicle_theft_report",
        "text": (
            "Δήλωση Κλοπής Οχήματος — ΑΤ Παγκρατίου\n"
            "Δηλών: Φωτεινή Παπακωνσταντίνου\n"
            "ΑΔΤ: ΑΞ-456789\n"
            "Όχημα: Toyota Yaris 2018, ΜΥΤ-0447\n"
            "VIN: JTDBL40E10J123456\n"
            "Δίπλ. οδήγησης 567891234\n"
            "Τόπος κλοπής: Παρκινγκ Hilton, Λεωφ. Βασ. Σοφίας 46\n"
            "Ημ.: 02/05/2026 23:45\n"
            "Τηλ.: 6987654321"
        ),
        "spans": [
            {"label": "private_person", "text": "Φωτεινή Παπακωνσταντίνου"},
            {"label": "adt", "text": "ΑΞ-456789"},
            {"label": "license_plate", "text": "ΜΥΤ-0447"},
            {"label": "vehicle_vin", "text": "JTDBL40E10J123456"},
            {"label": "driver_license", "text": "567891234"},
            {"label": "private_date", "text": "02/05/2026"},
            {"label": "private_phone", "text": "6987654321"},
        ],
    },
    {
        "id": 80,
        "register": "vehicle_warranty",
        "text": (
            "Εγγύηση Κατασκευαστή — BMW Hellas\n"
            "Όχημα: BMW X3, ΥΑΧ-5678, VIN WBA3A5C50DF234567\n"
            "Ιδιοκτήτης: Δημήτριος Καραμπίνας\n"
            "ΑΦΜ: 478125853\n"
            "Email: dim.karabinas@example.gr | Τηλ: 6987456321\n"
            "Έναρξη εγγύησης: 12/04/2026 | Λήξη: 12/04/2031\n"
            "Σύνδεση: bmw.gr/warranty-portal"
        ),
        "spans": [
            {"label": "license_plate", "text": "ΥΑΧ-5678"},
            {"label": "vehicle_vin", "text": "WBA3A5C50DF234567"},
            {"label": "private_person", "text": "Δημήτριος Καραμπίνας"},
            {"label": "afm", "text": "478125853"},
            {"label": "private_email", "text": "dim.karabinas@example.gr"},
            {"label": "private_phone", "text": "6987456321"},
            {"label": "private_date", "text": "12/04/2026"},
            {"label": "private_date", "text": "12/04/2031"},
            {"label": "private_url", "text": "bmw.gr/warranty-portal"},
        ],
    },
    # ============== EDUCATION / SCHOOL (81-90) ==============
    {
        "id": 81,
        "register": "school_enrollment",
        "text": (
            "Δημοτικό Σχολείο Παγκρατίου — Εγγραφή Μαθητή\n"
            "Μαθητής: Μάριος Παπαϊωάννου, γεν. 14/05/2018\n"
            "ΑΜΚΑ: 14051845678\n"
            "Πατέρας: Νικόλαος Παπαϊωάννου, ΑΦΜ 667112379\n"
            "Μητέρα: Ελένη Παπαϊωάννου, ΑΦΜ 991068097\n"
            "Διεύθυνση: Φιλελλήνων 14, 11635 Παγκράτι\n"
            "Email επικοινωνίας: papaioannou.family@example.gr | Τηλ: 6987234567"
        ),
        "spans": [
            {"label": "private_person", "text": "Μάριος Παπαϊωάννου"},
            {"label": "private_date", "text": "14/05/2018"},
            {"label": "amka", "text": "14051845678"},
            {"label": "private_person", "text": "Νικόλαος Παπαϊωάννου"},
            {"label": "afm", "text": "667112379"},
            {"label": "private_person", "text": "Ελένη Παπαϊωάννου"},
            {"label": "afm", "text": "991068097"},
            {"label": "private_address", "text": "Φιλελλήνων 14, 11635 Παγκράτι"},
            {"label": "private_email", "text": "papaioannou.family@example.gr"},
            {"label": "private_phone", "text": "6987234567"},
        ],
    },
    {
        "id": 82,
        "register": "university_admission",
        "text": (
            "Πανεπιστήμιο Αθηνών — Πιστοποιητικό Εγγραφής\n"
            "Φοιτητής: Στέφανος Καραντίνος\n"
            "ΑΜΚΑ: 24069326152\n"
            "Σχολή: Πληροφορικής & Τηλεπικοινωνιών\n"
            "Έτος: Α' (2026-2027)\n"
            "Διεύθυνση: Λεωφ. Αλεξάνδρας 132, 11522 Αθήνα\n"
            "Email φοιτητή: student.21031@uoa.gr\n"
            "Email προσωπικό: stefanos.karantinos@example.com\n"
            "Τηλ.: 6912345678"
        ),
        "spans": [
            {"label": "private_person", "text": "Στέφανος Καραντίνος"},
            {"label": "amka", "text": "24069326152"},
            {"label": "private_address", "text": "Λεωφ. Αλεξάνδρας 132, 11522 Αθήνα"},
            {"label": "private_email", "text": "student.21031@uoa.gr"},
            {"label": "private_email", "text": "stefanos.karantinos@example.com"},
            {"label": "private_phone", "text": "6912345678"},
        ],
    },
    {
        "id": 83,
        "register": "school_grades_email",
        "text": (
            "From: secretary@school-athens.edu.gr\n"
            "To: parent@example.com\n"
            "Θέμα: Βαθμολογία Α' Τετραμήνου - Μαθητής Κωνσταντίνος Παπαδάκης\n\n"
            "Αγαπητοί γονείς,\n"
            "Σας αποστέλλουμε τη βαθμολογία του παιδιού σας. ΑΜ Μαθητή: 2026-AT-12345\n"
            "Ονομαστικός μέσος όρος: 17.8\n"
            "Στοιχεία επικοινωνίας: 2103456789\n"
            "Email Δ/ντή: dimitris.papadopoulos@school-athens.edu.gr"
        ),
        "spans": [
            {"label": "private_email", "text": "secretary@school-athens.edu.gr"},
            {"label": "private_email", "text": "parent@example.com"},
            {"label": "private_person", "text": "Κωνσταντίνος Παπαδάκης"},
            {"label": "account_number", "text": "2026-AT-12345"},
            {"label": "private_phone", "text": "2103456789"},
            {"label": "private_email", "text": "dimitris.papadopoulos@school-athens.edu.gr"},
        ],
    },
    {
        "id": 84,
        "register": "tuition_receipt",
        "text": (
            "Ιδιωτικό Εκπαιδευτήριο Atlas ΑΕ — Απόδειξη Διδάκτρων\n"
            "Μαθητής: Δέσποινα Σωτηρίου\n"
            "Γονέας: Πέτρος Σωτηρίου, ΑΦΜ 386326581\n"
            "ΓΕΜΗ εταιρείας: 894206471379\n"
            "Ποσό: 6.500€ ετήσια\n"
            "Πληρωμή: IBAN GR09 0029 3345 1129 8333 9761 387\n"
            "Email: family.sotiriou@example.com\n"
            "Σχολικό έτος: 2026-2027\n"
            "Έκδοση: 15/06/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Δέσποινα Σωτηρίου"},
            {"label": "private_person", "text": "Πέτρος Σωτηρίου"},
            {"label": "afm", "text": "386326581"},
            {"label": "gemi", "text": "894206471379"},
            {"label": "iban_gr", "text": "GR09 0029 3345 1129 8333 9761 387"},
            {"label": "private_email", "text": "family.sotiriou@example.com"},
            {"label": "private_date", "text": "15/06/2026"},
        ],
    },
    {
        "id": 85,
        "register": "graduate_certificate",
        "text": (
            "Πτυχίο Πανεπιστημίου Κρήτης\n"
            "Όνομα: ΕΥΑΓΓΕΛΟΣ ΠΑΠΑΔΑΚΗΣ\n"
            "ΑΜΚΑ: 03058045678 | ΑΔΤ ΑΗ-654321\n"
            "Σχολή: Μηχανικών Η/Υ & Πληροφορικής\n"
            "Βαθμός Πτυχίου: 8.45\n"
            "Ημ. αποφοίτησης: 28/06/2025\n"
            "Γραμματεία: 2810394456 | Πιστοποιητικό αρ.: ΠΚ-2025-MEC-3478"
        ),
        "spans": [
            {"label": "private_person", "text": "ΕΥΑΓΓΕΛΟΣ ΠΑΠΑΔΑΚΗΣ"},
            {"label": "amka", "text": "03058045678"},
            {"label": "adt", "text": "ΑΗ-654321"},
            {"label": "private_date", "text": "28/06/2025"},
            {"label": "private_phone", "text": "2810394456"},
            {"label": "account_number", "text": "ΠΚ-2025-MEC-3478"},
        ],
    },
    {
        "id": 86,
        "register": "online_course_enrollment",
        "text": (
            "Coursera Hellas — Εγγραφή Online Μαθήματος\n"
            "Μαθητής: Ζωή Λεοντίδου\n"
            "Email: zoi.leontidou@example.gr\n"
            "Login URL: coursera.org/student/auth\n"
            "Πληρωμή 49€ με κάρτα 5536 8912 4567 8901 (CVV 567)\n"
            "Πιστοποιητικό αρ.: COUR-2026-A1B2\n"
            "Τηλ. εγγραφής: 6912345678"
        ),
        "spans": [
            {"label": "private_person", "text": "Ζωή Λεοντίδου"},
            {"label": "private_email", "text": "zoi.leontidou@example.gr"},
            {"label": "private_url", "text": "coursera.org/student/auth"},
            {"label": "card_pan", "text": "5536 8912 4567 8901"},
            {"label": "cvv", "text": "567"},
            {"label": "account_number", "text": "COUR-2026-A1B2"},
            {"label": "private_phone", "text": "6912345678"},
        ],
    },
    {
        "id": 87,
        "register": "research_grant_application",
        "text": (
            "ΕΛΙΔΕΚ — Αίτηση Ερευνητικού Προγράμματος\n"
            "Επιστημονικός Υπεύθυνος: Δρ. Γεώργιος Καραντινός\n"
            "ΑΦΜ: 045678912\n"
            "ΑΜΚΑ: 12058923456\n"
            "Email: g.karantinos@upatras.gr | Τηλ: 2610997123\n"
            "Πανεπιστήμιο: Πανεπιστήμιο Πατρών\n"
            "Πρόγραμμα: AI for Greek NLP, αρ. πρωτ. 2026/RES-789\n"
            "Ημ. υποβολής: 30/04/2026\n"
            "URL: elidek.gr/grants/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Γεώργιος Καραντινός"},
            {"label": "afm", "text": "045678912"},
            {"label": "amka", "text": "12058923456"},
            {"label": "private_email", "text": "g.karantinos@upatras.gr"},
            {"label": "private_phone", "text": "2610997123"},
            {"label": "account_number", "text": "2026/RES-789"},
            {"label": "private_date", "text": "30/04/2026"},
            {"label": "private_url", "text": "elidek.gr/grants/2026"},
        ],
    },
    {
        "id": 88,
        "register": "school_emergency_contact",
        "text": (
            "Έντυπο Επικοινωνίας Έκτακτης Ανάγκης\n"
            "Μαθητής: Στράτος Αντωνόπουλος\n"
            "Πατέρας: Δημήτρης Αντωνόπουλος, κιν. 6932456789, "
            "email d.antonopoulos@example.gr\n"
            "Μητέρα: Άννα Αντωνοπούλου, κιν. 6987654321\n"
            "Διεύθυνση: Λυκαβηττού 14, 10672 Αθήνα\n"
            "ΑΜΚΑ μαθητή: 11051545678\n"
            "Παιδίατρος: Δρ. Παππάς, τηλ 2103456789"
        ),
        "spans": [
            {"label": "private_person", "text": "Στράτος Αντωνόπουλος"},
            {"label": "private_person", "text": "Δημήτρης Αντωνόπουλος"},
            {"label": "private_phone", "text": "6932456789"},
            {"label": "private_email", "text": "d.antonopoulos@example.gr"},
            {"label": "private_person", "text": "Άννα Αντωνοπούλου"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "private_address", "text": "Λυκαβηττού 14, 10672 Αθήνα"},
            {"label": "amka", "text": "11051545678"},
            {"label": "private_person", "text": "Παππάς"},
            {"label": "private_phone", "text": "2103456789"},
        ],
    },
    {
        "id": 89,
        "register": "scholarship_award",
        "text": (
            "Ίδρυμα Ωνάση — Απονομή Υποτροφίας\n"
            "Δικαιούχος: Ευτυχία Λάμπρου\n"
            "ΑΦΜ: 200163042 | ΑΔΤ ΑΗ-789123\n"
            "ΑΜΚΑ: 30109056789 | ΠΑΠ: 738256104B89\n"
            "Πανεπιστήμιο: Harvard University\n"
            "Διαβατήριο: ΑΛ7234567\n"
            "Ποσό: 35.000€ ετήσια\n"
            "IBAN: GR74 1437 8069 1801 4717 0330 118\n"
            "Email: efty.lambrou@example.com\n"
            "Έναρξη: 01/09/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ευτυχία Λάμπρου"},
            {"label": "afm", "text": "200163042"},
            {"label": "adt", "text": "ΑΗ-789123"},
            {"label": "amka", "text": "30109056789"},
            {"label": "pcn", "text": "738256104B89"},
            {"label": "passport", "text": "ΑΛ7234567"},
            {"label": "iban_gr", "text": "GR74 1437 8069 1801 4717 0330 118"},
            {"label": "private_email", "text": "efty.lambrou@example.com"},
            {"label": "private_date", "text": "01/09/2026"},
        ],
    },
    {
        "id": 90,
        "register": "library_card_application",
        "text": (
            "Εθνική Βιβλιοθήκη — Έκδοση Κάρτας Μέλους\n"
            "Όνομα: Ηλίας Παπαδημητρίου\n"
            "ΑΔΤ ΙΙ-690868 | Διεύθυνση Σόλωνος 78, 10680 Αθήνα\n"
            "Email: ilias.p@example.gr | Τηλ: 6987654321\n"
            "ΠΑΠ: 234918725W63\n"
            "Αρ. κάρτας μέλους: NLG-MEM-456789\n"
            "Ημ. έκδοσης: 22/04/2026"
        ),
        "spans": [
            {"label": "private_person", "text": "Ηλίας Παπαδημητρίου"},
            {"label": "adt", "text": "ΙΙ-690868"},
            {"label": "private_address", "text": "Σόλωνος 78, 10680 Αθήνα"},
            {"label": "private_email", "text": "ilias.p@example.gr"},
            {"label": "private_phone", "text": "6987654321"},
            {"label": "pcn", "text": "234918725W63"},
            {"label": "account_number", "text": "NLG-MEM-456789"},
            {"label": "private_date", "text": "22/04/2026"},
        ],
    },
    # ============== INFORMAL / SMS (91-100) ==============
    {
        "id": 91,
        "register": "informal_sms_meet",
        "text": (
            "Hey Γιάννη! Έχεις χρόνο να βρεθούμε αύριο στις 18:30 στο café Veneti στην "
            "Σταδίου 25; Θέλω να σου δείξω τα αποτελέσματα. Αν χάσω, καλέστε με στο "
            "6970-123456 ή στείλε email στο giannis.k@meetup.io. Φιλικά, Στέφανος"
        ),
        "spans": [
            {"label": "private_person", "text": "Γιάννη"},
            {"label": "private_address", "text": "Σταδίου 25"},
            {"label": "private_phone", "text": "6970-123456"},
            {"label": "private_email", "text": "giannis.k@meetup.io"},
            {"label": "private_person", "text": "Στέφανος"},
        ],
    },
    {
        "id": 92,
        "register": "informal_messenger_split_bill",
        "text": (
            "Άκου Λένα, για το δείπνο χτες, θες να μου στείλεις 35€ στο IBAN μου;\n"
            "GR95 8381 5575 1303 3454 6273 571\n"
            "Ή Revolut στο email lena.f@example.com\n"
            "Τσεκάρε και τη φωτό απόδειξης που σου έστειλα στις 14/05/2026."
        ),
        "spans": [
            {"label": "private_person", "text": "Λένα"},
            {"label": "iban_gr", "text": "GR95 8381 5575 1303 3454 6273 571"},
            {"label": "private_email", "text": "lena.f@example.com"},
            {"label": "private_date", "text": "14/05/2026"},
        ],
    },
    {
        "id": 93,
        "register": "viber_emergency_contact",
        "text": (
            "ΦΠΑΞΕ ΚΑΛΑ ΑΥΤΟΝ ΤΟΝ ΑΡΙΘΜΟ:\n"
            "Δρ Παναγιώτου, παιδίατρος, 2103456712\n"
            "Κινητό: 6932561234\n"
            "Διεύθυνση: Λεωφ. Κηφισίας 234, Κηφισιά (πάνω από Public.gr)\n"
            "Επείγον email: dr.panagiotou@example.com"
        ),
        "spans": [
            {"label": "private_person", "text": "Παναγιώτου"},
            {"label": "private_phone", "text": "2103456712"},
            {"label": "private_phone", "text": "6932561234"},
            {"label": "private_address", "text": "Λεωφ. Κηφισίας 234, Κηφισιά"},
            {"label": "private_email", "text": "dr.panagiotou@example.com"},
        ],
    },
    {
        "id": 94,
        "register": "informal_invoice_request",
        "text": (
            "ΥΓ: Αποστολή τιμολογίου: ΓΕΜΗ 145678300000, ΑΦΜ 246514326.\n"
            "Παραλήπτης: Αλέξης Σ. Καπετανίδης\n"
            "Διεύθυνση τιμολόγησης: Σόλωνος 23, 10672 Αθήνα\n"
            "Email: alexis.kap@example.com"
        ),
        "spans": [
            {"label": "gemi", "text": "145678300000"},
            {"label": "afm", "text": "246514326"},
            {"label": "private_person", "text": "Αλέξης Σ. Καπετανίδης"},
            {"label": "private_address", "text": "Σόλωνος 23, 10672 Αθήνα"},
            {"label": "private_email", "text": "alexis.kap@example.com"},
        ],
    },
    {
        "id": 95,
        "register": "informal_password_share_warning",
        "text": (
            "Μάκη μη το πεις πουθενά, αλλά ο νέος κωδικός του router είναι "
            "WiFi_Home_2026!Strong\n"
            "Και το Netflix password: NetflixFamily_pwd@2026\n"
            "Mέσα στο Mac MAC AB:CD:EF:12:34:56 για να μη ξεχάσεις"
        ),
        "spans": [
            {"label": "private_person", "text": "Μάκη"},
            {"label": "secret", "text": "WiFi_Home_2026!Strong"},
            {"label": "secret", "text": "NetflixFamily_pwd@2026"},
            {"label": "mac_address", "text": "AB:CD:EF:12:34:56"},
        ],
    },
    {
        "id": 96,
        "register": "informal_doctor_referral",
        "text": (
            "Ρε Νίκο, σου στέλνω παραπεμπτικό για τον φίλο σου τον Πέτρο. "
            "ΑΜΚΑ: 17089034567, ΑΦΜ 574528922. Πάει στον Δρ Καρρά την Τετάρτη "
            "12/06/2026 στις 15:00. Καλέστε ξανά τον Πέτρο στο 6912345678 να "
            "επιβεβαιώσει."
        ),
        "spans": [
            {"label": "private_person", "text": "Νίκο"},
            {"label": "private_person", "text": "Πέτρο"},
            {"label": "amka", "text": "17089034567"},
            {"label": "afm", "text": "574528922"},
            {"label": "private_person", "text": "Καρρά"},
            {"label": "private_date", "text": "12/06/2026"},
            {"label": "private_phone", "text": "6912345678"},
        ],
    },
    {
        "id": 97,
        "register": "informal_lost_dog_post",
        "text": (
            "🆘 Χάθηκε ο σκύλος μου από Παγκράτι 14/05/2026!\n"
            "Όνομα: Ρόκι (Husky), 5 ετών\n"
            "Microchip: 941000012345678\n"
            "Όποιος τον δει ας τηλεφωνήσει στο 6987234567 (Άρτεμις) ή στο "
            "artemis.dog@example.gr. Αμοιβή 200€!"
        ),
        "spans": [
            {"label": "private_date", "text": "14/05/2026"},
            {"label": "private_phone", "text": "6987234567"},
            {"label": "private_person", "text": "Άρτεμις"},
            {"label": "private_email", "text": "artemis.dog@example.gr"},
        ],
    },
    {
        "id": 98,
        "register": "informal_meet_directions",
        "text": (
            "Πάμε στις 8 το βράδυ στο σπίτι μου: Ηπείρου 47, 11251 Αθήνα, "
            "3ος όροφος. Διπλωμα οδήγησης 349085520 αν θες να φέρεις το "
            "αμάξι. Πάρε με στο 6987654321 αν χαθείς."
        ),
        "spans": [
            {"label": "private_address", "text": "Ηπείρου 47, 11251 Αθήνα"},
            {"label": "driver_license", "text": "349085520"},
            {"label": "private_phone", "text": "6987654321"},
        ],
    },
    {
        "id": 99,
        "register": "informal_dating_chat",
        "text": (
            "Γεια Στεφανία! Σε λένε Στεφανία Κακογιάννη σωστά; Ευχαρίστως αύριο! "
            "Πάμε για cocktail στο Booze; Στείλε μου το instagram σου ή το email "
            "σου να συνδεθούμε. Εγώ είμαι ο Δημήτρης (dimitris.x@example.gr, "
            "6987234561). Πάμε στις 21:00 στις 16/05/2026?"
        ),
        "spans": [
            {"label": "private_person", "text": "Στεφανία"},
            {"label": "private_person", "text": "Στεφανία Κακογιάννη"},
            {"label": "private_person", "text": "Δημήτρης"},
            {"label": "private_email", "text": "dimitris.x@example.gr"},
            {"label": "private_phone", "text": "6987234561"},
            {"label": "private_date", "text": "16/05/2026"},
        ],
    },
    {
        "id": 100,
        "register": "informal_dense_pii_chaos",
        "text": (
            "Άκου ρε φίλε, μπορείς να βάλεις ως επαφή τον γιατρό μου;\n"
            "Δρ. Δημητρίου Παναγιώτης, ΑΦΜ 500415967, AΔΤ ΩΞ-616673\n"
            "Διεύθυνση: Σκουφά 23, 10672 Αθήνα\n"
            "Τηλ.: 2103456712 / Κιν: 6932451768\n"
            "Email: dimitriou.dr@example.com\n"
            "Site: https://drdimitriou.gr/contact\n"
            "Στις επείγουσες, MAC του φορητού του είναι 00:1A:2B:3C:4D:5E "
            "και IP 192.168.1.45 αν χρειαστείς remote desktop. Thx!"
        ),
        "spans": [
            {"label": "private_person", "text": "Δημητρίου Παναγιώτης"},
            {"label": "afm", "text": "500415967"},
            {"label": "adt", "text": "ΩΞ-616673"},
            {"label": "private_address", "text": "Σκουφά 23, 10672 Αθήνα"},
            {"label": "private_phone", "text": "2103456712"},
            {"label": "private_phone", "text": "6932451768"},
            {"label": "private_email", "text": "dimitriou.dr@example.com"},
            {"label": "private_url", "text": "https://drdimitriou.gr/contact"},
            {"label": "mac_address", "text": "00:1A:2B:3C:4D:5E"},
            {"label": "ip_address", "text": "192.168.1.45"},
        ],
    },
]
