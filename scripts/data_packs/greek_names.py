"""Greek names + declension engine for the privacy-filter v2.5 person pack.

Provides 100+ Greek surnames, 50+ male + 50+ female first names, and
rule-based inflection that produces nominative / genitive / accusative /
vocative forms. Patterns cover the major Greek surname endings:
  -ος, -ης, -ας, -ίδης, -όπουλος, -άκης, -άτος, -ιάδης, -άκος, -έας

Inflection rules are deterministic per ending. Vocative formation is
captured per ending pattern. Female surnames are derived from male roots
via standard Greek conventions (-ος → -ου for daughter form genitive,
-ης → -η, -άκης → -άκη).

Usage:
    from greek_names import inflect_name, MALE_FIRST_NAMES, FEMALE_FIRST_NAMES, SURNAMES_M
    forms = inflect_name("Παπαδόπουλος", gender="m")
    # → {"nom": "Παπαδόπουλος", "gen": "Παπαδόπουλου", "acc": "Παπαδόπουλο", "voc": "Παπαδόπουλε"}
"""
from __future__ import annotations

from dataclasses import dataclass

# ─── Surname master lists ─────────────────────────────────────────────

# Common male root forms. Not exhaustive — covers ~12 distinct ending
# patterns enough to cover most real-world Greek surnames.
SURNAMES_M = [
    # -ος ending
    "Παπαδόπουλος", "Αντωνόπουλος", "Δημόπουλος", "Παππάς",
    "Νικολόπουλος", "Καραντώνης", "Κωνσταντίνου", "Σταυρόπουλος",
    "Λαμπρόπουλος", "Γεωργόπουλος", "Στρατόπουλος", "Ζαχαρόπουλος",
    "Ασημακόπουλος", "Φωτόπουλος", "Σταματόπουλος", "Παναγιωτόπουλος",
    "Χριστόπουλος", "Πετρόπουλος", "Ηλιόπουλος", "Καλοπούλος",
    # -ίδης ending
    "Ιωαννίδης", "Νικολαΐδης", "Παπαδημητρίου", "Κωνσταντινίδης",
    "Σαμαρίδης", "Στεφανίδης", "Καραντωνίδης", "Δημητρίδης",
    "Ζαχαρίδης", "Παπαζαφειρίδης", "Στράτος", "Στρατάκης",
    # -άκης ending
    "Νικολάκης", "Δημητράκης", "Παπαδάκης", "Καραντωνάκης",
    "Σταυράκης", "Λαμπράκης", "Γεωργιάκης", "Σαμαράκης",
    # -ης ending
    "Καραντώνης", "Σαμαράς", "Αλεξίου", "Αναστασίου",
    "Παπαναστασίου", "Καλογεράς", "Δημητριάδης", "Ζαχαρίας",
    # -όπουλος / specific
    "Καρρά", "Μαρκόπουλος", "Σταματάκης", "Κωνσταντινάκης",
    "Παπαθανασίου", "Παπακωνσταντίνου", "Παπαδημητρίου", "Παπανικολάου",
    "Παπαθεοδώρου", "Παπαδόπουλος", "Παπασταυρόπουλος", "Παπαϊωάννου",
    # other patterns
    "Βλάχος", "Λύκος", "Καρρέλας", "Παππάς", "Ζαχαρίας",
    "Νικολαΐδης", "Σαρβανίδης", "Πατούλης", "Παπαζαφείρης",
    "Χατζηγιάννης", "Χριστοδούλου", "Ξανθόπουλος", "Καρανίκας",
    "Δημουλάς", "Σταματιάδης", "Καραμέρος", "Θεοδωρόπουλος",
    "Σπανός", "Στρατάκης", "Παύλου", "Καλλίας",
    # legal/business common
    "Καρακώστας", "Πετράκης", "Μηλιαρέσης", "Λεοντίδης",
    "Λάππας", "Σωτηριάδης", "Πυρομάλλης", "Καραντώνης",
    "Λεμπέσης", "Φραντζής", "Ζώτος", "Κωτσιόπουλος",
    "Χάλαρης", "Λάλας", "Σαμαρτζής", "Πασχαλίδης",
    "Μαστοράκης", "Νικολούδης", "Καραγιάννης", "Καζαντζάκης",
    "Παπαμιχαλόπουλος", "Λουκαρέλης", "Πορφυριάδης",
]

# Female surnames in Greek typically derive from the male form: many
# are just the male form in the *genitive* (e.g. Παπαδόπουλος → η
# Παπαδοπούλου). The list below provides explicit female forms for
# the most common surnames; the inflection engine also synthesises
# female forms for surnames not in this list.
SURNAMES_F = [
    "Παπαδοπούλου", "Αντωνοπούλου", "Δημοπούλου", "Παππά",
    "Νικολοπούλου", "Καραντώνη", "Κωνσταντίνου", "Σταυροπούλου",
    "Λαμπροπούλου", "Γεωργοπούλου", "Στρατοπούλου", "Ζαχαροπούλου",
    "Ασημακοπούλου", "Φωτοπούλου", "Σταματοπούλου", "Παναγιωτοπούλου",
    "Χριστοπούλου", "Πετροπούλου", "Ηλιοπούλου", "Καλοπούλου",
    "Ιωαννίδου", "Νικολαΐδου", "Παπαδημητρίου", "Κωνσταντινίδου",
    "Σαμαρίδου", "Στεφανίδου", "Καραντωνίδου", "Δημητρίδου",
    "Νικολάκη", "Δημητράκη", "Παπαδάκη", "Καραντωνάκη",
    "Σταυράκη", "Λαμπράκη", "Γεωργιάκη", "Σαμαράκη",
    "Σαμαρά", "Αλεξίου", "Αναστασίου", "Παπαναστασίου",
    "Καλογερά", "Δημητριάδη", "Ζαχαρία", "Καρρά",
    "Μαρκοπούλου", "Σταματάκη", "Κωνσταντινάκη", "Παπαθανασίου",
    "Παπακωνσταντίνου", "Παπαδημητρίου", "Παπανικολάου", "Παπαθεοδώρου",
    "Παπασταυροπούλου", "Παπαϊωάννου", "Βλάχου", "Λύκου",
    "Καρρέλα", "Χατζηγιάννη", "Χριστοδούλου", "Ξανθοπούλου",
    "Καρανίκα", "Δημουλά", "Σταματιάδη", "Καραμέρου",
    "Θεοδωροπούλου", "Σπανού", "Παύλου", "Καλλία",
    "Καρακώστα", "Πετράκη", "Μηλιαρέση", "Λεοντίδου",
    "Λάππα", "Σωτηριάδη", "Πυρομάλλη", "Λεμπέση",
]

# ─── First-name master lists ───────────────────────────────────────────

MALE_FIRST_NAMES = [
    "Γιώργος", "Νίκος", "Δημήτρης", "Αντώνης", "Παναγιώτης", "Κώστας",
    "Στέλιος", "Βασίλης", "Θανάσης", "Γιάννης", "Στράτος", "Παύλος",
    "Σπύρος", "Δήμος", "Λευτέρης", "Άρης", "Ηλίας", "Μιχάλης",
    "Στάθης", "Πέτρος", "Φώτης", "Χρήστος", "Σωτήρης", "Λάμπρος",
    "Ηρακλής", "Κύριλλος", "Φίλιππος", "Λεωνίδας", "Στέργιος",
    "Πελοπίδας", "Ιάκωβος", "Νικόλαος", "Δημήτριος", "Αναστάσιος",
    "Σταύρος", "Ευάγγελος", "Θεοδόσιος", "Θεόδωρος", "Διονύσιος",
    "Βαρθολομαίος", "Κωνσταντίνος", "Ανδρέας", "Σαράντος",
    "Αλέξανδρος", "Ιωάννης", "Πασχάλης", "Εμμανουήλ", "Μάριος",
    "Νεκτάριος", "Σωκράτης", "Παρασκευάς", "Λυκούργος",
    "Αριστοτέλης", "Άκης", "Στέφανος", "Χαράλαμπος",
]

FEMALE_FIRST_NAMES = [
    "Μαρία", "Ελένη", "Κατερίνα", "Σοφία", "Χριστίνα", "Αθηνά",
    "Ιωάννα", "Αγγελική", "Δήμητρα", "Δέσποινα", "Φωτεινή", "Ευτυχία",
    "Νεκταρία", "Παρασκευή", "Ανδριάνα", "Αναστασία", "Ηρώ",
    "Χρυσούλα", "Ευαγγελία", "Σταυρούλα", "Καλλιόπη", "Μαρίνα",
    "Πηνελόπη", "Στυλιανή", "Πελαγία", "Αικατερίνη", "Νίκη",
    "Στεφανία", "Φιλομήλα", "Ανθούλα", "Άννα", "Μαρίνα",
    "Ευφροσύνη", "Φοίβη", "Στέλλα", "Ξανθή", "Ολυμπία",
    "Δάφνη", "Μυρσίνη", "Γεωργία", "Βασιλική", "Διονυσία",
    "Χαρά", "Τζένη", "Φανή", "Αλεξάνδρα", "Ευαγγελία",
    "Ευγενία", "Λαμπρινή", "Στυλιανή", "Νατάσσα", "Ελισάβετ",
    "Καλλισθένη", "Καλλιόπη", "Ζωή", "Φωτεινή", "Ναταλία",
]

# ─── Inflection engine ────────────────────────────────────────────────

# Surname inflection — handle common Greek surname endings.
# Each rule: (suffix_match, gen_replacement, acc_replacement, voc_replacement)
# Applied in order — first match wins.

_SURNAME_RULES_M = [
    # -όπουλος → -όπουλου / -όπουλο / -όπουλε
    ("όπουλος", "όπουλου", "όπουλο", "όπουλε"),
    # -ίδης → -ίδη / -ίδη / -ίδη  (genitive: -ίδη)
    ("ίδης", "ίδη", "ίδη", "ίδη"),
    # -ιάδης → -ιάδη
    ("ιάδης", "ιάδη", "ιάδη", "ιάδη"),
    # -άκης → -άκη
    ("άκης", "άκη", "άκη", "άκη"),
    # -άκος → -άκου / -άκο / -άκο
    ("άκος", "άκου", "άκο", "άκο"),
    # -άτος → -άτου / -άτο / -άτο
    ("άτος", "άτου", "άτο", "άτο"),
    # -έας → -έα / -έα / -έα
    ("έας", "έα", "έα", "έα"),
    # -ιάς → -ιά / -ιά / -ιά
    ("ιάς", "ιά", "ιά", "ιά"),
    # -άς → -ά / -ά / -ά
    ("άς", "ά", "ά", "ά"),
    # -ής → -ή
    ("ής", "ή", "ή", "ή"),
    # -ος → -ου / -ο / -ε  (general -ος rule)
    ("ος", "ου", "ο", "ε"),
    # -ης → -η
    ("ης", "η", "η", "η"),
    # -ίας → -ία (Ζαχαρίας → Ζαχαρία)
    ("ίας", "ία", "ία", "ία"),
    # -ου → -ου (already genitive form, no inflection)
    ("ου", "ου", "ου", "ου"),
]

_SURNAME_RULES_F = [
    # Female surnames typically don't decline — same form across cases
    # except sometimes nominative vs genitive differs slightly.
    # Most common: keep same form for all four cases.
    ("ου", "ου", "ου", "ου"),
    ("η", "η", "η", "η"),
    ("α", "ας", "α", "α"),
    ("ίδου", "ίδου", "ίδου", "ίδου"),
]

# First-name inflection — only handles common patterns. Coverage is
# imperfect but captures >80% of common Greek first names.

_FIRST_NAME_RULES_M = [
    # -ος → -ου / -ο / -ε
    ("ος", "ου", "ο", "ε"),
    # -ης → -η
    ("ης", "η", "η", "η"),
    # -ας → -α
    ("ας", "α", "α", "α"),
    # -ής → -ή
    ("ής", "ή", "ή", "ή"),
    # -ίδης → -ίδη
    ("ίδης", "ίδη", "ίδη", "ίδη"),
]

_FIRST_NAME_RULES_F = [
    # -α → -ας / -α / -α
    ("α", "ας", "α", "α"),
    # -η → -ης / -η / -η
    ("η", "ης", "η", "η"),
    # -ώ → -ώς (only for "Ηρώ" etc.)
    ("ώ", "ώς", "ώ", "ώ"),
]


def _apply_rules(name: str, rules: list[tuple]) -> dict[str, str]:
    """Apply inflection rules to a name. Returns dict with nom/gen/acc/voc."""
    nom = name
    for suffix, gen_repl, acc_repl, voc_repl in rules:
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            return {
                "nom": nom,
                "gen": stem + gen_repl,
                "acc": stem + acc_repl,
                "voc": stem + voc_repl,
            }
    # Fallback: no inflection (returns same form for all cases)
    return {"nom": nom, "gen": nom, "acc": nom, "voc": nom}


def inflect_surname(name: str, gender: str = "m") -> dict[str, str]:
    rules = _SURNAME_RULES_M if gender == "m" else _SURNAME_RULES_F
    return _apply_rules(name, rules)


def inflect_first_name(name: str, gender: str = "m") -> dict[str, str]:
    rules = _FIRST_NAME_RULES_M if gender == "m" else _FIRST_NAME_RULES_F
    return _apply_rules(name, rules)


# ─── Title prefixes ───────────────────────────────────────────────────

TITLES_M = [
    ("κ.", "voc"),
    ("κύριος", "nom"),
    ("κύριο", "acc"),
    ("κύριε", "voc"),
    ("κυρίου", "gen"),
    ("Δρ.", "nom"),
    ("Καθ.", "nom"),
    ("Καθηγητής", "nom"),
    ("ο", "nom"),
    ("του", "gen"),
    ("τον", "acc"),
]

TITLES_F = [
    ("κα.", "voc"),
    ("κυρία", "nom"),
    ("κυρίας", "gen"),
    ("κυρίαν", "acc"),
    ("Δρ.", "nom"),
    ("Καθ.", "nom"),
    ("Καθηγήτρια", "nom"),
    ("η", "nom"),
    ("της", "gen"),
    ("την", "acc"),
]


@dataclass(frozen=True)
class InflectedName:
    """Output of name composition: full name string + the case used."""
    text: str
    case: str  # "nom" / "gen" / "acc" / "voc"
    gender: str  # "m" / "f"
    components: dict


def compose_name(
    rng,
    *,
    gender: str | None = None,
    case: str | None = None,
    include_title: bool = False,
    first_only: bool = False,
    last_only: bool = False,
    last_first_order: bool = False,
) -> InflectedName:
    """Compose a single full-name string with optional title.

    Each name returned: case (nom/gen/acc/voc) is uniformly random unless
    forced. Title prefix optional. first_only/last_only return single
    component. last_first_order swaps to surname-first style.
    """
    if gender is None:
        gender = rng.choice(["m", "f"])
    if case is None:
        case = rng.choice(["nom", "gen", "acc", "voc"])

    first_pool = MALE_FIRST_NAMES if gender == "m" else FEMALE_FIRST_NAMES
    surname_pool = SURNAMES_M if gender == "m" else SURNAMES_F

    first_root = rng.choice(first_pool)
    surname_root = rng.choice(surname_pool)

    first_forms = inflect_first_name(first_root, gender)
    surname_forms = inflect_surname(surname_root, gender)

    first = first_forms[case]
    surname = surname_forms[case]

    if first_only:
        text = first
    elif last_only:
        text = surname
    elif last_first_order:
        text = f"{surname} {first}"
    else:
        text = f"{first} {surname}"

    if include_title and not first_only and not last_only:
        title_pool = TITLES_M if gender == "m" else TITLES_F
        # Filter titles compatible with the chosen case (if marked)
        # Some titles work in any context — so just pick one.
        title, _ = rng.choice(title_pool)
        text = f"{title} {text}"

    return InflectedName(
        text=text,
        case=case,
        gender=gender,
        components={"first": first, "surname": surname,
                    "first_root": first_root, "surname_root": surname_root},
    )
