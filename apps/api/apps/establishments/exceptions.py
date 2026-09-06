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


class CohortAlreadyExists(DomainError):
    """Code-review fix (2026-09, closing out Story 6.5) — `Cohort` gained a
    `(establishment, name, school_year)` uniqueness constraint (migration
    0004) with no data path to catch it cleanly; a double-submit / two
    admins racing used to be a raw `IntegrityError` -> 500.
    """

    type = "https://path-advisor.fr/errors/cohort-already-exists"
    title = "Cohorte déjà existante"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Une cohorte avec ce nom existe déjà pour cet établissement et cette année."


class StudentNotInCounselorsEstablishment(DomainError):
    """Story 6.7 — a counselor tried to request consent for a student
    outside their own establishment (`StudentImportInvitation.cohort.
    establishment` must match the counselor's own `tenant_id`)."""

    type = "https://path-advisor.fr/errors/student-not-in-establishment"
    title = "Élève hors de ton établissement"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Cet élève n'appartient pas à ton établissement."


class ConsentCooldownActive(DomainError):
    """Story 6.7 AC — a counselor tried to re-request consent within 7 days
    of a refusal."""

    type = "https://path-advisor.fr/errors/consent-cooldown-active"
    title = "Nouvelle demande impossible pour l'instant"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = (
        "L'élève a refusé récemment — tu peux redemander le consentement dans quelques jours."
    )


class ConsentNotGranted(DomainError):
    """Story 6.7/6.8 — a counselor tried to view an individual profile
    without a `granted`, non-revoked `CounselorConsent`."""

    type = "https://path-advisor.fr/errors/consent-not-granted"
    title = "Consentement requis"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Cet élève n'a pas encore donné son accord pour que tu consultes son profil."


class ConsentAlreadyDecided(DomainError):
    """Story 6.7 — a student tried to decide a consent request that isn't
    (or is no longer) pending."""

    type = "https://path-advisor.fr/errors/consent-already-decided"
    title = "Demande déjà traitée"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cette demande a déjà été traitée."


class CounselorEmailAlreadyRegistered(DomainError):
    """Code-review fix (2026-09, closing out Story 6.5) — accepting a
    counselor invitation whose `invitation.email` already belongs to
    another `User` row (e.g. the same person invited twice, or the email
    already used by a student/parent account) used to bubble up as an
    uncaught `IntegrityError` -> 500, instead of a clean typed response.
    """

    type = "https://path-advisor.fr/errors/email-already-registered"
    title = "Email déjà utilisé"
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Un compte existe déjà avec cette adresse email. Contacte l'équipe Path-Advisor."
    )
