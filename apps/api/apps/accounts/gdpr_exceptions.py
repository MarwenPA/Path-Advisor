"""GDPR-export-specific `DomainError` subclasses (Story 1.11).

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
        "Tu as déjà demandé un export il y a moins de 24 heures. "
        "Patiente avant d'en redemander un."
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
