"""RFC 7807 Problem Details — domain exceptions + DRF handler.

Convention (core-architectural-decisions §API): every 4xx/5xx response that the
front consumes is shaped as `application/problem+json` with `type`, `title`,
`status`, `detail`, `instance` (request path), and optional `errors`.

Add a new error here whenever a story introduces a domain failure mode that the
front needs to disambiguate (e.g. show a specific message or deep-link). Free-
text errors must never leak through — they are unactionable for clients.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
)
from rest_framework.exceptions import (
    PermissionDenied as DRFPermissionDenied,
)
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


class DomainError(Exception):
    """Root of Path-Advisor business errors. Sub-class per failure mode."""

    type: str = "https://path-advisor.fr/errors/unknown"
    title: str = "Domain error"
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_detail: str = "An error occurred."

    # When True, `extras` are rendered as Problem Details TOP-LEVEL extensions
    # (RFC 7807 §3.2) instead of nested under `body.errors`. Use this for
    # routing hints, retry-after-style fields, or anything that is NOT a
    # field-level validation error. Default False preserves the pre-Story-1.5
    # behavior (extras → `errors`) for existing callers.
    extras_as_extensions: bool = False

    def __init__(self, detail: str | None = None, **extras: object) -> None:
        super().__init__(detail or self.default_detail)
        self.detail: str = detail or self.default_detail
        self.extras: dict[str, object] = dict(extras)


class AgeUnder15(DomainError):
    # Retained as a fall-through for the rare case where `parent_email` is missing
    # AND the consent_rgpd path is hit before the per-field branch (Story 1.3 backstop).
    # Normal sub-15 signups go through ParentEmailRequired (Story 1.4).
    type = "https://path-advisor.fr/errors/age-under-15"
    title = "Inscription mineur sous 15 ans"
    default_detail = "L'inscription des moins de 15 ans nécessite l'email d'un parent ou tuteur."


class ParentEmailRequired(DomainError):
    # Sub-15 signup without a parent_email — the front must show the conditional field.
    type = "https://path-advisor.fr/errors/parent-email-required"
    title = "Email parent requis pour les moins de 15 ans"
    default_detail = (
        "Pour ton âge, nous avons besoin de l'email d'un parent ou tuteur pour "
        "valider ton inscription."
    )


class ParentEmailNotApplicable(DomainError):
    # Strict guard: prevent ≥ 15 signups from silently carrying a parent_email field.
    # Keeps Story 1.3's happy path immutable and surfaces front-end form mismatches early.
    type = "https://path-advisor.fr/errors/parent-email-not-applicable"
    title = "Email parent non applicable"
    default_detail = "L'email d'un parent n'est requis que pour les moins de 15 ans."


class ParentEmailSameAsStudent(DomainError):
    type = "https://path-advisor.fr/errors/parent-email-same-as-student"
    title = "Email parent identique"
    default_detail = "Ton parent ne peut pas avoir la même adresse email que toi."


class ParentalConsentNotFound(DomainError):
    type = "https://path-advisor.fr/errors/parental-consent-not-found"
    title = "Lien invalide ou expiré"
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Ce lien d'autorisation parentale n'existe pas ou a expiré."


class ParentalConsentAlreadyDecided(DomainError):
    # Single-use semantics on the decision: once granted or refused, the token is locked.
    # 60-day window also blocks the parent post-expiry; same status, distinct UX.
    type = "https://path-advisor.fr/errors/parental-consent-already-decided"
    title = "Décision déjà enregistrée"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cette demande a déjà reçu une décision ou a expiré."


class EmailAlreadyRegistered(DomainError):
    # The `type` URI is allowed to be specific (the front-end keys off it to route to a
    # "try logging in instead" UX) — but `title` and `default_detail` MUST stay generic.
    # Title leaks via Problem Details just like field-level errors do (CWE-203).
    type = "https://path-advisor.fr/errors/email-already-registered"
    title = "Inscription impossible"
    default_detail = "Impossible de créer un compte avec ces informations."


class ConsentRgpdRequired(DomainError):
    type = "https://path-advisor.fr/errors/consent-rgpd-required"
    title = "Consentement RGPD requis"
    default_detail = "Tu dois accepter les CGU et la politique RGPD pour continuer."


class WeakPassword(DomainError):
    type = "https://path-advisor.fr/errors/weak-password"
    title = "Mot de passe trop faible"
    default_detail = "Le mot de passe ne respecte pas les règles de sécurité."


class RateLimited(DomainError):
    type = "https://path-advisor.fr/errors/rate-limited"
    title = "Trop de tentatives"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Trop de tentatives. Réessaie dans quelques minutes."


class EmailTokenInvalid(DomainError):
    type = "https://path-advisor.fr/errors/email-token-invalid"
    title = "Lien expiré ou déjà utilisé"
    default_detail = "Ce lien de vérification est invalide. Demande-en un nouveau."


class AuditLogImmutable(DomainError):
    # Audit entries are append-only at both the ORM layer and the DB trigger layer.
    # Hitting this exception is an incident — never a normal flow.
    type = "https://path-advisor.fr/errors/audit-log-immutable"
    title = "Journal d'audit immuable"
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Les entrées du journal d'audit ne peuvent être ni modifiées ni supprimées."


class InsufficientPermissions(DomainError):
    type = "https://path-advisor.fr/errors/insufficient-permissions"
    title = "Permission insuffisante"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Vous n'avez pas l'autorisation d'accéder à cette ressource."


def path_advisor_exception_handler(exc: Exception, context: dict) -> Response | None:
    """DRF exception handler — converts DomainError + DRF ValidationError to Problem JSON."""

    request_path = context["request"].path if context.get("request") else ""

    # Sentry alert on any audit tamper attempt — these are NEVER expected in normal flow.
    if isinstance(exc, AuditLogImmutable):
        try:
            import sentry_sdk

            sentry_sdk.capture_message(
                f"audit.tamper_attempt: {exc.detail}",
                level="error",
            )
        except Exception:
            pass

    if isinstance(exc, DomainError):
        problem = {
            "type": exc.type,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request_path,
        }
        if exc.extras:
            if exc.extras_as_extensions:
                # RFC 7807 §3.2: extension members live at the top level.
                # Used by `EmailNotVerified` (resend_endpoint routing hint)
                # so it does not pretend to be a field-level validation error.
                problem.update(exc.extras)
            else:
                problem["errors"] = exc.extras
        response = Response(problem, status=exc.status_code)
        response["Content-Type"] = "application/problem+json"
        if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            response["Retry-After"] = str(exc.extras.get("retry_after_seconds", 3600))
        return response

    # Convert DRF's default `PermissionDenied` to our typed Problem so any 403
    # in the API carries `type=…/insufficient-permissions`. Story 1.13 AC5.
    if isinstance(exc, DRFPermissionDenied):
        typed = InsufficientPermissions(detail=str(exc.detail) if exc.detail else None)
        problem = {
            "type": typed.type,
            "title": typed.title,
            "status": typed.status_code,
            "detail": typed.detail,
            "instance": request_path,
        }
        response = Response(
            problem, status=typed.status_code, content_type="application/problem+json"
        )
        response["Content-Type"] = "application/problem+json"
        return response

    # Same treatment for 401s coming from `IsAuthenticated`.
    if isinstance(exc, NotAuthenticated):
        problem = {
            "type": "https://path-advisor.fr/errors/not-authenticated",
            "title": "Authentification requise",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": str(exc.detail) if exc.detail else "Vous devez vous connecter.",
            "instance": request_path,
        }
        response = Response(problem, status=status.HTTP_401_UNAUTHORIZED)
        response["Content-Type"] = "application/problem+json"
        return response

    if isinstance(exc, DRFValidationError):
        # Flatten DRF's nested {"field": ["msg1", "msg2"]} to a Problem with errors map.
        problem = {
            "type": "https://path-advisor.fr/errors/validation",
            "title": "Validation échouée",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": "Une ou plusieurs valeurs sont invalides.",
            "instance": request_path,
            "errors": exc.detail,
        }
        response = Response(problem, status=status.HTTP_400_BAD_REQUEST)
        response["Content-Type"] = "application/problem+json"
        return response

    # Fall back to DRF's default for everything else (auth errors, 5xx, etc.).
    return drf_default_handler(exc, context)
