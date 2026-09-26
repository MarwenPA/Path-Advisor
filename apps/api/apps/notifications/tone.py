"""Epic 8 — the executable calm-tone contract, in ONE importable place.

Revue Epic 8 (P3): the banned-marker lists had drifted between the story
lints (8.5/8.6 missed `dépêche`/`attention`; 8.6 missed `pas retenu`) — a
future "Attention !" would have passed CI on the digest and the cards.
Every tone lint imports from here; adding a marker instantly covers every
surface already under test. The front mirrors these in
`apps/web/src/lib/i18n/tone.test.ts` (keep in sync by hand — two runtimes).

`attention` is bounded to `[ !,.]` on purpose: the seed referential uses
"Mais attention :" in a profession description (informative register, not a
notification) — the lints only run on notification surfaces anyway, the
bound just keeps the regex honest about what it targets.
"""

from __future__ import annotations

#: UX-DR28 — urgency/pressure markers banned from EVERY student-facing
#: notification surface (email subjects, txt, html, DeltaRecap cards).
URGENCY_MARKERS = [
    r"derni[eè]re chance",
    r"plus que \d+",
    r"\bvite\b",
    r"\burgent",
    r"!!",
    r"d[ée]p[êe]che",
    r"ne (rate|manque) pas",
    r"attention[ !,.]",
    # Anti-cirque (8.6 AC: « pas confetti, pas 🎉 »).
    r"🎉",
    r"bravo !",
]

#: 8.4 — the negative school response must stay constructive: banned from
#: the not_aligned email variant AND the not_aligned DeltaRecap card.
NOT_ALIGNED_MARKERS = [
    r"mauvaise nouvelle",
    r"malheureusement",
    r"\brefus",
    r"rejet",
    r"échec",
    r"pas retenu",
]
