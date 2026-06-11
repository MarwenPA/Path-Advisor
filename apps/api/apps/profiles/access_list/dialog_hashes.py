"""Canonical revoke-dialog content hashes — Story 1.10 §AC8 + §T5.

Reuses the Story 1.14 pattern : the frontend renders a fixed-shape consent
dialog ; the SHA-256 of its content is sent in the POST body and the backend
compares against the value stored here. Any copy drift between frontend and
backend fails ``test_revoke_dialog_hash_matches_frontend`` loudly — forcing
the dev to validate the new wording before shipping.

Per-tier hashes : parent / school / counselor each get one canonical payload.
School and counselor are placeholders for Stories 5.4 / 6.7 — their revoke
flow lands when those stories ship. The hash is computed from a JSON-stable
representation (``sort_keys=True``, no whitespace).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .dto import TierType

#: Canonical 8-field payload per tier. The frontend renders these strings
#: verbatim ; the SHA-256 of `json.dumps(payload, sort_keys=True,
#: separators=(",", ":"))` is the contract.
CANONICAL_REVOKE_DIALOG_PAYLOADS: dict[TierType, dict[str, Any]] = {
    "parent": {
        "version": "1.0",
        "title": "Révoquer l'accès de ton parent",
        "subtitle": "Tu peux retirer cet accès à tout moment.",
        "consequence_main": "Ton parent ne verra plus tes métiers explorés ni tes parcours sauvegardés.",
        "consequence_secondary": "Ses paiements premium éventuels restent valides jusqu'à leur terme.",
        "confirmation_label": "Je confirme révoquer cet accès",
        "primary_cta": "Révoquer l'accès",
        "secondary_cta": "Annuler",
    },
    "school": {
        "version": "1.0",
        "title": "Révoquer l'accès de l'école",
        "subtitle": "Tu peux retirer cet accès à tout moment.",
        "consequence_main": "L'école perd l'accès à ta fiche profil immédiatement.",
        "consequence_secondary": "Les réponses qu'elle a déjà émises restent dans ton historique.",
        "confirmation_label": "Je confirme révoquer cet accès",
        "primary_cta": "Révoquer l'accès",
        "secondary_cta": "Annuler",
    },
    "counselor": {
        "version": "1.0",
        "title": "Révoquer l'accès de ta conseillère",
        "subtitle": "Tu peux retirer cet accès à tout moment.",
        "consequence_main": "Ta conseillère ne verra plus ton profil détaillé.",
        "consequence_secondary": "Ses notes anonymisées dans son tableau de cohorte restent visibles pour elle.",
        "confirmation_label": "Je confirme révoquer cet accès",
        "primary_cta": "Révoquer l'accès",
        "secondary_cta": "Annuler",
    },
}


def compute_dialog_hash(payload: dict[str, Any]) -> str:
    """SHA-256 of the canonical JSON serialization. Frontend MUST use the same
    serialization (sort_keys, compact separators)."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


#: Pre-computed per-tier hashes — the value the POST body's ``content_hash``
#: MUST equal for the revoke to proceed.
CANONICAL_REVOKE_DIALOG_HASHES: dict[TierType, str] = {
    tier: compute_dialog_hash(payload) for tier, payload in CANONICAL_REVOKE_DIALOG_PAYLOADS.items()
}
