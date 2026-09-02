"""Establishments-app domain errors — Story 6.5.

Sub-classes `apps.core.exceptions.DomainError` (RFC 7807 handler, zero
changes needed to `apps/core/exceptions.py`) — same pattern as
`apps.family.exceptions`.
"""

from __future__ import annotations

from rest_framework import status

from apps.core.exceptions import DomainError


class EstablishmentUaiAlreadyTaken(DomainError):
    type = "https://path-advisor.fr/errors/establishment-uai-taken"
    title = "UAI déjà utilisé"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Un établissement avec cet UAI existe déjà — vérifie qu'il ne s'agit pas d'un doublon d'onboarding."


class CsvTooManyRows(DomainError):
    type = "https://path-advisor.fr/errors/csv-too-many-rows"
    title = "Fichier trop volumineux"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Le fichier CSV dépasse la limite de 2000 lignes par import."


class InvitationNotFoundOrExpired(DomainError):
    type = "https://path-advisor.fr/errors/invitation-not-found"
    title = "Lien invalide ou expiré"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Ce lien d'invitation n'est plus valide."
