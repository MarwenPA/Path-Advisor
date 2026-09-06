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
