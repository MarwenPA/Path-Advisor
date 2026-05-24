"""GDPR-specific `DomainError` subclasses — Stories 1.11 (export) and 1.12 (erasure).

Each error maps to one Problem Details `type` URI the front can switch on to
display a specific message or remediation flow. Keep them out of
`apps.core.exceptions` so the core module stays free of feature-specific
clutter — only generic / cross-cutting errors live there.
"""

from __future__ import annotations

from rest_framework import status

from apps.core.exceptions import DomainError


class GdprExportError(DomainError):
    """Base class for all GDPR-export failures — never raised directly."""

    type = "https://path-advisor.fr/errors/gdpr-export"
    title = "Export RGPD"
    default_detail = "Une erreur est survenue sur ta demande d'export."


class GdprExportInProgress(GdprExportError):
    type = "https://path-advisor.fr/errors/gdpr-export-in-progress"
    title = "Demande d'export en cours"
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Une demande d'export est déjà en cours pour ton compte. "
        "Patiente jusqu'à sa complétion (max 30 minutes)."
    )


class GdprExportRateLimited(GdprExportError):
    type = "https://path-advisor.fr/errors/gdpr-export-rate-limited"
    title = "Délai entre exports non écoulé"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = (
        "Tu as déjà demandé un export il y a moins de 24 heures. Patiente avant d'en redemander un."
    )


class GdprExportNotReady(GdprExportError):
    type = "https://path-advisor.fr/errors/gdpr-export-not-ready"
    title = "Export pas encore prêt"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Cet export n'est pas encore prêt."


class GdprExportExpired(GdprExportError):
    type = "https://path-advisor.fr/errors/gdpr-export-expired"
    title = "Export expiré"
    status_code = status.HTTP_410_GONE
    default_detail = (
        "Ce lien d'export a expiré. Demande un nouvel export pour récupérer tes données."
    )


class GdprExportDownloadCap(GdprExportError):
    type = "https://path-advisor.fr/errors/gdpr-export-download-cap"
    title = "Nombre de téléchargements dépassé"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Cet export a atteint le nombre maximum de téléchargements autorisés."


# ---------------------------------------------------------------------------
# Story 1.12 — Account deletion (GDPR Article 17, right to erasure)
# ---------------------------------------------------------------------------


class AccountDeletionError(DomainError):
    """Base class for the account-deletion failure modes — never raised directly."""

    type = "https://path-advisor.fr/errors/account-deletion"
    title = "Suppression de compte"
    default_detail = "Une erreur est survenue sur ta demande de suppression."


class InvalidPassword(AccountDeletionError):
    # Generic 400 reused by both the request flow (AC1) and the cancel flow (AC5).
    # Generic title to avoid leaking that the password specifically (vs another
    # field) was the issue — CWE-203 hygiene mirroring `EmailAlreadyRegistered`.
    type = "https://path-advisor.fr/errors/invalid-password"
    title = "Mot de passe incorrect"
    default_detail = "Vérifie ton mot de passe et réessaye."


class AccountDeletionAlreadyPending(AccountDeletionError):
    type = "https://path-advisor.fr/errors/account-deletion-already-pending"
    title = "Une demande de suppression est déjà en cours"
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Une demande de suppression de ton compte est déjà en cours. "
        "Vérifie ton email pour le lien d'annulation."
    )


class AccountDeletionAlreadyResolved(AccountDeletionError):
    type = "https://path-advisor.fr/errors/account-deletion-already-resolved"
    title = "Demande déjà traitée"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cette demande a déjà été annulée ou exécutée."


class AccountDeletionExpired(AccountDeletionError):
    type = "https://path-advisor.fr/errors/account-deletion-expired"
    title = "Fenêtre d'annulation expirée"
    status_code = status.HTTP_410_GONE
    default_detail = (
        "Le délai de 30 jours pour annuler cette suppression est dépassé. "
        "Tu peux créer un nouveau compte si tu le souhaites."
    )


class AccountDeletionNotFound(AccountDeletionError):
    type = "https://path-advisor.fr/errors/account-deletion-not-found"
    title = "Lien invalide ou expiré"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Ce lien d'annulation est invalide ou expiré."


class AccountDeletionNoPending(AccountDeletionError):
    """No in-flight deletion for the authenticated user (Story 1.12 code review §P17).

    Distinct from `AccountDeletionNotFound` (which is the public-token endpoint
    "unknown token" path) — the authenticated `/me/account-deletion/status/`
    endpoint uses this so clients switching on `type` can differentiate the
    two 404 semantics.
    """

    type = "https://path-advisor.fr/errors/account-deletion-no-pending"
    title = "Aucune suppression en cours"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tu n'as pas de demande de suppression en cours."


class AccountDeleted(AccountDeletionError):
    """Surfaced by the login adapter when a user with `status=DELETED` attempts to sign in.

    The 403 is intentional (vs the default 401 from `is_active=False`) so the front
    can detect the deletion state and route to the cancel-flow info page. The detail
    string avoids leaking whether the email exists pre-deletion — uniform with the
    `EmailAlreadyRegistered` enumeration-resistance policy.
    """

    type = "https://path-advisor.fr/errors/account-deleted"
    title = "Compte supprimé"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "Ce compte est désactivé. "
        "Si tu n'as pas demandé cette suppression, vérifie tes emails pour annuler."
    )
