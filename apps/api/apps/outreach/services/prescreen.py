"""Story 9.4 — automatic pre-screening of free text under moderation.

An AID for prioritisation, NEVER a decision (AC: « la décision finale est
toujours humaine — pas d'auto-refus »). Two families of flags:
- `pii`: third-party personal data patterns (emails, French phone numbers,
  URLs) — the AC's « données personnelles détectées »;
- `risk`: a deliberately SHORT lexicon of slurs/violence markers. Short on
  purpose: a long blocklist rots and over-flags; the human reads anyway.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+", re.I)
_PHONE_FR = re.compile(r"(?:\+33|0)\s*[1-9](?:[\s.-]?\d{2}){4}")
_URL = re.compile(r"https?://\S+|www\.\S+", re.I)

#: Volontairement court — marqueurs de haine/violence/discrimination.
_RISK_WORDS = [
    r"\bcon(?:ne|nard|nasse)s?\b",
    r"\bencul",
    r"\bpute?s?\b",
    r"\bsalope?s?\b",
    r"\bni[qk]u?e",
    r"\bpd\b",
    r"\bsale\s+(arabe|noir|juif|blanc|chinois)",
    r"\btuer\b|\bfrapper\b|\bviolence\b",
    r"\bsuicid",
]
_RISK = [re.compile(pattern, re.I) for pattern in _RISK_WORDS]


def prescreen_text(text: str) -> dict[str, list[str]]:
    """Return {'pii': [...], 'risk': [...]} — empty lists mean nothing found."""
    text = text or ""
    pii: list[str] = []
    if _EMAIL.search(text):
        pii.append("email")
    if _PHONE_FR.search(text):
        pii.append("telephone")
    if _URL.search(text):
        pii.append("url")
    risk = sorted({match.group(0).lower() for rx in _RISK for match in [rx.search(text)] if match})
    return {"pii": pii, "risk": risk}
