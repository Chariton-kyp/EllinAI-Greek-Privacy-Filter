"""ELOT 743 / ISO 843-style Greek-to-Latin transliteration.

Used to keep rule-generated emails and URLs realistic: Greek given
names should be transliterated to Latin for the email-local-part and
URL-slug portions, even though the display-name span (private_person)
remains in Greek script.
"""
from __future__ import annotations

import unicodedata


_GREEK_TO_LATIN: dict[str, str] = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z",
    "η": "i", "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m",
    "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "ch", "ψ": "ps",
    "ω": "o",
}


def transliterate_greek(text: str) -> str:
    """Return a best-effort Latin transliteration of `text`.

    Non-Greek characters pass through unchanged. Diacritics are stripped
    before mapping (ώ → ο → o, etc.).
    """
    stripped = unicodedata.normalize("NFD", text)
    stripped = "".join(
        c for c in stripped if unicodedata.category(c) != "Mn"
    )
    out: list[str] = []
    for c in stripped:
        lower = c.lower()
        rep = _GREEK_TO_LATIN.get(lower)
        if rep is None:
            out.append(c)
            continue
        if c.isupper():
            rep = rep[0].upper() + rep[1:] if len(rep) > 1 else rep.upper()
        out.append(rep)
    return "".join(out)
