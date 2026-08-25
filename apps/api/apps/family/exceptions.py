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


class ParentInvitationEmailMismatch(DomainError):
    """Code-review finding (2026-08) — the token is the sole proof of
    authorization for this endpoint, but nothing previously constrained the
    resulting account to the invited email. Raised when:
    - the anonymous accept body supplies an `email` different from
      `invitation.parent_email` (AC3 says the email is "pre-filled,
      non-editable" — the backend must enforce that, not just the frontend), or
    - an already-authenticated `role="parent"` user (AC4) tries to accept an
      invitation addressed to a different email than their own account.
    """

    type = "https://path-advisor.fr/errors/parent-invitation-email-mismatch"
    title = "Email non conforme à l'invitation"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "Cette invitation a été envoyée à une autre adresse — "
        "connecte-toi avec le compte correspondant pour l'accepter."
    )


class ParentInvitationResendRateLimited(DomainError):
    type = "https://path-advisor.fr/errors/parent-invitation-rate-limited"
    title = "Trop de renvois"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Tu as déjà renvoyé cette invitation récemment. Réessaie dans une heure."


class ParentNotLinkedToStudent(DomainError):
    """Story 6.2 §AC4 — the parent holds no active `ParentStudentLink` to the
    requested student. The non-revoked link is the SOLE authorization source
    (Story 6.1 §AC7): no fallback on email or tenant.
    """

    type = "https://path-advisor.fr/errors/parent-not-linked"
    title = "Accès non autorisé"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Tu n'as pas accès au profil de cet élève."


class ParentBulletinsForbidden(DomainError):
    """Story 6.2 §AC3 — a parent (even a linked one) may never read a child's
    bulletins / teacher appreciations (FR41 / NFR-S4). Always 403 + audit.
    """

    type = "https://path-advisor.fr/errors/parent-bulletins-forbidden"
    title = "Bulletins non accessibles"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "Les bulletins et appréciations de ton enfant restent privés — "
        "ils ne sont jamais accessibles depuis un compte parent."
    )
