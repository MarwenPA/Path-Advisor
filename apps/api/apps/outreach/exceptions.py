"""Outreach-app domain errors — Story 5.4.

Sub-classes `apps.core.exceptions.DomainError` (RFC 7807 handler) — same
pattern as `apps.establishments.exceptions`/`apps.family.exceptions`.
"""

from __future__ import annotations

from rest_framework import status

from apps.core.exceptions import DomainError


class MonthlyOutreachQuotaExceeded(DomainError):
    """AC3 — non-anxiogenic copy: informs, doesn't scold. `default_detail`
    is the exact wording the story mandates."""

    type = "https://path-advisor.fr/errors/outreach-quota-exceeded"
    title = "Quota d'envois atteint"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = (
        "Tu as utilisé tes 5 envois ce mois — ta limite repart le 1er du mois prochain."
    )


class OutreachModerationStateError(DomainError):
    """Story 5.5 — a moderation action (approve/reject/resubmit) was
    attempted on a request that isn't in the state it requires (e.g.
    approving a request that's already `pending`, or resubmitting one
    that isn't `rejected`)."""

    type = "https://path-advisor.fr/errors/outreach-moderation-state"
    title = "Action de modération impossible dans cet état"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cette demande n'est pas dans un état permettant cette action."
