# Benchmark Failure Mining

- Checkpoint: `/workspace/artifacts/finetune-v2-12-20260430T094120Z/model`
- Decoder: `viterbi`
- Aggregate F1: `0.8266`
- Precision / recall: `0.8814` / `0.7781`

## Priorities

| label | score | F1 | P | R | missed | confusion | boundary | hallucinated | pack |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| private_person | 123 | 0.782 | 0.872 | 0.708 | 32 | 2 | 8 | 5 | qwen_narrative/person_vocative_polytonic: surnames, vocatives, titles, two-person messages |
| private_email | 54 | 0.782 | 0.896 | 0.694 | 14 | 2 | 3 | 0 | qwen_contrastive/email_vs_secret: normal email plus adjacent token/key-like strings |
| private_phone | 39 | 0.737 | 0.800 | 0.683 | 6 | 7 | 0 | 0 | qwen_contrastive/phone_vs_account: phone markers and account markers in the same record |
| amka | 35 | 0.667 | 0.867 | 0.542 | 11 | 0 | 0 | 2 | qwen_narrative/amka_administrative: dense Greek admin prose with nearby numeric confusables |
| afm | 27 | 0.894 | 0.977 | 0.824 | 8 | 1 | 0 | 0 | qwen_narrative/afm_administrative: dense Greek admin prose with nearby numeric confusables |
| ip_address | 19 | 0.741 | 0.909 | 0.625 | 6 | 0 | 0 | 1 | qwen_contrastive/ip_address_technical_or_payment: same-record positive plus numeric confusable |
| private_date | 19 | 0.886 | 0.897 | 0.875 | 5 | 0 | 0 | 4 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| mac_address | 13 | 0.583 | 0.583 | 0.583 | 0 | 3 | 2 | 0 | qwen_contrastive/mac_vs_ip_vs_vin: network logs with MAC, IP, VIN-like device ids |
| ama | 13 | 0.783 | 0.900 | 0.692 | 4 | 0 | 0 | 1 | qwen_narrative/ama_administrative: dense Greek admin prose with nearby numeric confusables |
| private_address | 12 | 0.881 | 0.860 | 0.902 | 1 | 0 | 3 | 3 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| cvv | 10 | 0.778 | 0.875 | 0.700 | 3 | 0 | 0 | 1 | qwen_contrastive/cvv_technical_or_payment: same-record positive plus numeric confusable |
| card_pan | 10 | 0.788 | 0.765 | 0.812 | 1 | 1 | 1 | 2 | qwen_contrastive/card_pan_technical_or_payment: same-record positive plus numeric confusable |
| driver_license | 10 | 0.818 | 0.900 | 0.750 | 3 | 0 | 0 | 1 | qwen_narrative/driver_license_administrative: dense Greek admin prose with nearby numeric confusables |
| adt | 10 | 0.917 | 0.957 | 0.880 | 3 | 0 | 0 | 1 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| private_url | 9 | 0.889 | 0.909 | 0.870 | 2 | 0 | 1 | 1 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| secret | 6 | 0.727 | 0.667 | 0.800 | 0 | 0 | 2 | 2 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| imei | 6 | 0.857 | 0.857 | 0.857 | 0 | 2 | 0 | 0 | qwen_contrastive/imei_technical_or_payment: same-record positive plus numeric confusable |
| passport | 6 | 0.889 | 1.000 | 0.800 | 2 | 0 | 0 | 0 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| license_plate | 4 | 0.933 | 0.933 | 0.933 | 1 | 0 | 0 | 1 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| gemi | 3 | 0.966 | 1.000 | 0.933 | 1 | 0 | 0 | 0 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| vehicle_vin | 2 | 0.889 | 0.889 | 0.889 | 0 | 0 | 1 | 0 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| account_number | 2 | 0.889 | 0.800 | 1.000 | 0 | 0 | 0 | 2 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |
| iban_gr | 1 | 0.973 | 0.947 | 1.000 | 0 | 0 | 0 | 1 | small_qwen_narrative_pack: 300-1000 local Qwen records, then ablate |

## Top Confusions

- `private_phone->account_number`: 7
- `mac_address->vehicle_vin`: 2
- `imei->account_number`: 2
- `private_email->secret`: 2
- `private_person->private_address`: 1
- `private_person->private_email`: 1
- `card_pan->iban_gr`: 1
- `afm->driver_license`: 1
- `mac_address->ip_address`: 1

## Example Misses

### private_person
- case `1` / `tax_form_letter`: `Παπαδοπούλου` in `Αξιότιμη κα Παπαδοπούλου,\n\nΗ Διεύθυνση Φορολογίας ΔΟΥ Α' Αθηνών σα`
- case `3` / `tax_office_email`: `Μάρκου` in `u@example.gr\nΘέμα: Εκκρεμότητα ΦΠΑ\n\nΚύριε Μάρκου, η εταιρεία σας με ΓΕΜΗ 089451200000 και `
- case `27` / `prescription`: `Ηλίας Σταματόπουλος` in `Συνταγή για: Ηλίας Σταματόπουλος, ΑΜΚΑ 09058723456. Φάρμακο: Atorvastatin `
- case `30` / `appointment_confirm_sms`: `Καρρά` in `Ραντεβού 15:30 την Τρίτη 18/05/2026, Δρ. Καρρά. ΑΜΚΑ 25067843219. Διεύθυνση κλινικής: Δο`
- case `39` / `job_application`: `Δημήτρης-Παύλος Βλάχος` in `Βιογραφικό υποψηφίου Δημήτρης-Παύλος Βλάχος, dimvlachos@protonmail.com, 6951234567. Δ`

### private_date
- case `2` / `tax_sms_short`: `30/06/2026` in `ΕΝΦΙΑ 2026: Πληρωμή έως 30/06/2026. ΑΦΜ: 087451209. Στοιχεία: gov.gr/enfia`
- case `64` / `b2b_contract`: `01/04/2026` in `ΕΜΗ 345672300000). Διάρκεια: 24 μήνες από 01/04/2026.`
- case `167` / `prose_news_anon`: `14 Απριλίου 2026` in `ωστή δημοσιογράφος, ανακοίνωσε χθες, στις 14 Απριλίου 2026, ότι αποχωρεί από τα ΜΜΕ. Δηλώθηκε στο Τμ`
- case `168` / `long_medical_history`: `12/05/1972` in `ικό ασθενούς. Όνομα: Σταύρος Καρρά (γενν. 12/05/1972, ΑΜΚΑ 12057245678). Δείκτες πίεσης φυσιολ`
- case `186` / `ergani_form`: `15/05/2026` in ` ΑΜΑ ΙΚΑ: 5678012. ΑΦΜ: 167823945. Έναρξη 15/05/2026.`

### private_url
- case `2` / `tax_sms_short`: `gov.gr/enfia` in `έως 30/06/2026. ΑΦΜ: 087451209. Στοιχεία: gov.gr/enfia`
- case `19` / `it_incident_log`: `https://vpn.company.gr/login` in `D:EE:01. User: alice@company.gr. Endpoint https://vpn.company.gr/login.`

### afm
- case `4` / `tax_authority_record`: `156234897` in `γουμένου\nΌνομα: Δημήτριος Στεφανίδης\nΑΦΜ: 156234897 | ΑΜΚΑ: 03128956712 | ΑΔΤ: ΞΗ-456789\nΔ/νσ`
- case `11` / `loan_application`: `234567891` in `Αιτών: Παύλος Δημόπουλος, ΑΦΜ 234567891. Λογαριασμός μισθοδοσίας: 7012-34567-890.`
- case `53` / `id_doc_compare`: `156789012` in ` Διαβατήριο AΕ8901234, ΑΔΤ ΞΞ-901234, ΑΦΜ 156789012. Όνομα: Παναγιώτης Σταματίου.`
- case `96` / `property_tax_notice`: `198234561` in ` Καλλιθέα. Ιδιοκτήτης Στέφανος Καρρά, ΑΦΜ 198234561. Ποσό: 487€.`
- case `128` / `power_of_attorney`: `098765431` in `Ιωάννης Παπαδημητρίου, ΑΔΤ ΖΞ-345678, ΑΦΜ 098765431. Πληρεξούσιος: Ευαγγελία Νικολάου, ΑΔΤ ΑΘ`

### driver_license
- case `13` / `vehicle_insurance_policy`: `845721369` in `ισμένος: Γιώργος Παππάς, δίπλωμα οδήγησης 845721369.`
- case `141` / `multi_pii_form`: `234578102` in `Η εταιρείας 245678300000 | Διπλ. οδήγησης 234578102 | IBAN GR1606601200004567812345678 | Τηλ.`
- case `190` / `vehicle_full_record`: `234567891` in `ταντίνου, ΑΦΜ 198765432, Δίπλωμα οδήγησης 234567891.`

### private_address
- case `17` / `stolen_vehicle_report`: `Ομήρου 18, Παγκράτι` in `ρ. πλαισίου TMBJF41Z7B2098765 από την οδό Ομήρου 18, Παγκράτι.`

### private_email
- case `20` / `api_key_leak`: `security@firm.gr` in `yjWDarjtT1zdp7dc στο repo. Επικοινωνία με security@firm.gr για άμεση ανάκληση.`
- case `24` / `firewall_rule`: `netops@company.gr` in `MAC source 00:1A:2B:3C:4D:5E. Approved by netops@company.gr.`
- case `43` / `egov_login`: `helpdesk@gov.gr` in `μφανίζονται οι υπηρεσίες σας. Επικοινωνία helpdesk@gov.gr.`
- case `80` / `salary_deposit_notice`: `payroll@enterprise.gr` in ` Καρρά (ΑΜΑ ΙΚΑ 6789012). Επιβεβαίωση στο payroll@enterprise.gr.`
- case `86` / `internal_doc_secret`: `access@company.gr` in `ProdK3y_a4b8c2d6e0f1g5h9i3j7. Restrict to access@company.gr.`

### ip_address
- case `21` / `system_admin_email`: `192.168.10.45` in `Νέος server pinned at 192.168.10.45. Admin: admin.ops@netcorp.gr. Κωδ. πρόσβα`
- case `24` / `firewall_rule`: `195.78.234.10` in `Allow inbound TCP/443 from 195.78.234.10 to 10.10.20.50, MAC source 00:1A:2B:3C:4D`
- case `24` / `firewall_rule`: `10.10.20.50` in `low inbound TCP/443 from 195.78.234.10 to 10.10.20.50, MAC source 00:1A:2B:3C:4D:5E. Approved b`
- case `107` / `ssh_dst_log`: `78.123.45.67` in `SSH connection from 78.123.45.67 to bastion 10.0.0.5 on port 22. User: ops`
- case `107` / `ssh_dst_log`: `10.0.0.5` in `H connection from 78.123.45.67 to bastion 10.0.0.5 on port 22. User: ops-greek-2026. Geoloca`

### amka
- case `25` / `medical_referral`: `14076512345` in `Ασθενής: Αλέξανδρος Παρασκευόπουλος, ΑΜΚΑ 14076512345, ηλικίας 50 ετών. Διεύθυνση: Ευελπίδων 24`
- case `27` / `prescription`: `09058723456` in `Συνταγή για: Ηλίας Σταματόπουλος, ΑΜΚΑ 09058723456. Φάρμακο: Atorvastatin 20mg, 1 δισκίο/ημέ`
- case `44` / `social_benefit_application`: `14056712345` in `ς: Νικολέτα Καρρά, ΠΑΠ 234561987Z45, ΑΜΚΑ 14056712345. Καταβολή στον IBAN GR1102601200000045671`
- case `47` / `covid_certificate`: `16078512345` in `ήτρης Παπαδάκης. ΠΑΠ: 098765432Q03. ΑΜΚΑ: 16078512345.`
- case `87` / `ama_card_renewal`: `12056712345` in `υστάθιος Σαμαράς. ΑΜΑ ΙΚΑ: 4567823. ΑΜΚΑ: 12056712345. Διεύθυνση: Θηβών 23, Πετρούπολη.`

### private_phone
- case `25` / `medical_referral`: `6932145678` in `ν. Διεύθυνση: Ευελπίδων 24, Κυψέλη. Τηλ.: 6932145678.`
- case `32` / `mobile_contract`: `6940987654` in ` Παύλος Καραβίτης, ΑΦΜ 167823945, αρ. SIM 6940987654.`
- case `37` / `hr_email_signature`: `6944112233` in `s@enterprise.gr\nΤηλ.: 210-9876543 | Κιν.: 6944112233\nΛεωφ. Κηφισίας 124, 11526 Αμπελόκηποι`
- case `117` / `carrier_unlock`: `6942345678` in `hone 14 Pro. Κάτοχος: Ηρώ Κωσταρίδη, τηλ. 6942345678.`
- case `121` / `support_ticket_open`: `6912345670` in `ικόλαος Παπαθανασίου, ΑΦΜ 187654321, τηλ. 6912345670.`

### passport
- case `33` / `passport_application`: `AΒ4567321` in ` αιτούντος: Φωτεινή Καλογήρου, διαβατήριο AΒ4567321 (παλαιό), ημ. γέννησης 22 Ιουλίου 1990, δ`
- case `54` / `passport_renewal_email`: `AΗ5678901` in `Παρελήφθη η αίτηση ανανέωσης διαβατηρίου AΗ5678901. Στοιχεία: Γιάννα Στράφορη (giannastrafor`

### ama
- case `36` / `employment_contract`: `9876543` in `612000) και του Νεκτάριου Βασιλείου, ΑΦΜ 198765432, ΑΜΑ ΙΚΑ 9876543. Έναρξη: 1η Ιουνίου 202`
- case `87` / `ama_card_renewal`: `4567823` in `. Δικαιούχος: Ευστάθιος Σαμαράς. ΑΜΑ ΙΚΑ: 4567823. ΑΜΚΑ: 12056712345. Διεύθυνση: Θηβών 23, `
- case `184` / `ika_branch_letter`: `4567890` in `ρώνουμε ότι ο νέος ΑΜΑ ασφαλισμένου είναι 4567890. Επικοινωνία: ika.athens@efka.gr.`
- case `186` / `ergani_form`: `5678012` in `ης. Εργαζόμενος: Στυλιανή Παππά. ΑΜΑ ΙΚΑ: 5678012. ΑΦΜ: 167823945. Έναρξη 15/05/2026.`

### cvv
- case `57` / `subscription_signup`: `504` in `δημητρίου. Κάρτα 4485 7821 6543 2109, CVC 504. Email: npapad@gmail.com.`
- case `58` / `refund_request`: `162` in ` στην κάρτα 5234 6789 1098 7654 (3-ψήφιος 162). Δικαιούχος: Σοφία Νικολαΐδου, IBAN GR83`
- case `59` / `atm_card_request`: `738` in `ρεωστική κάρτα 4921 5678 9012 3456 με CVV 738 παραδίδεται στη διεύθυνση Ναυαρίνου 8, 10`

### card_pan
- case `58` / `refund_request`: `5234 6789 1098 7654` in `Επιστροφή χρημάτων στην κάρτα 5234 6789 1098 7654 (3-ψήφιος 162). Δικαιούχος: Σοφία Νικολαΐ`

### license_plate
- case `104` / `driver_change_form`: `ΖΕΥ-7821` in `Αλλαγή οδηγού στο όχημα ΖΕΥ-7821. Νέος οδηγός: Παναγιώτης Ζαχαρόπουλος, δί`

### adt
- case `128` / `power_of_attorney`: `ΖΞ-345678` in `ρεξουσιοδότης: Ιωάννης Παπαδημητρίου, ΑΔΤ ΖΞ-345678, ΑΦΜ 098765431. Πληρεξούσιος: Ευαγγελία Ν`
- case `128` / `power_of_attorney`: `ΑΘ-901234` in `31. Πληρεξούσιος: Ευαγγελία Νικολάου, ΑΔΤ ΑΘ-901234.`
- case `141` / `multi_pii_form`: `ΑΖ-345678` in ` | ΑΦΜ 087654321 | ΑΜΚΑ 03127895432 | ΑΔΤ ΑΖ-345678 | ΓΕΜΗ εταιρείας 245678300000 | Διπλ. οδή`

### gemi
- case `141` / `multi_pii_form`: `245678300000` in `27895432 | ΑΔΤ ΑΖ-345678 | ΓΕΜΗ εταιρείας 245678300000 | Διπλ. οδήγησης 234578102 | IBAN GR16066`
