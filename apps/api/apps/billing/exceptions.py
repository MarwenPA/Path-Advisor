"""Billing-app domain errors — Story 5.3.

Sub-classes `apps.core.exceptions.DomainError` so they flow through the
existing RFC 7807 Problem Details handler with zero changes elsewhere.
"""

from __future__ import annotations

from rest_framework import status

from apps.core.exceptions import DomainError


class NoActiveSubscription(DomainError):
    """Story 5.3 AC3 — cancellation requested but the user has no active
    (or already-scheduled-to-cancel) premium subscription to act on."""

    type = "https://path-advisor.fr/errors/no-active-subscription"
    title = "Aucun abonnement actif"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tu n'as pas d'abonnement premium actif à annuler."
