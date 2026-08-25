"""Family-app domain errors — Story 6.1.

Sub-classes `apps.core.exceptions.DomainError` so they flow through the
existing RFC 7807 Problem Details handler (`path_advisor_exception_handler`)
with zero changes to `apps/core/exceptions.py`.
"""

from __future__ import annotations

from rest_framework import status

from apps.core.exceptions import DomainError


class ParentInvitationAlreadyPending(DomainError):
    type = "https://path-advisor.fr/errors/parent-invitation-already-pending"
    title = "Invitation déjà en attente"
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Une invitation est déjà en attente pour cet email — "
        "tu peux la renvoyer depuis 'Mes proches'."
    )


class ParentInvitationNotFoundOrExpired(DomainError):
    type = "https://path-advisor.fr/errors/parent-invitation-not-found"
    title = "Lien invalide ou expiré"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Ce lien d'invitation n'est plus valide."


class ParentInvitationEmailTaken(DomainError):
    type = "https://path-advisor.fr/errors/parent-invitation-email-taken"
    title = "Compte déjà existant"
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Un compte existe déjà avec cet email — connecte-toi puis accepte "
        "l'invitation depuis ton compte."
    )


class ParentInvitationResendRateLimited(DomainError):
    type = "https://path-advisor.fr/errors/parent-invitation-rate-limited"
    title = "Trop de renvois"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Tu as déjà renvoyé cette invitation récemment. Réessaie dans une heure."
