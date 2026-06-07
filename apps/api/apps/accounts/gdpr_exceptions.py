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


# ---------------------------------------------------------------------------
# Story 1.5 — Login flow exceptions
#
# Note: this module is now broader than its name suggests (covers all auth
# Problem Details since Story 1.12 added AccountDeleted). Rename to
# `auth_exceptions.py` flagged as deferred-work in Story 1.5 §6 #2.
# ---------------------------------------------------------------------------


class AccountLocked(AccountDeletionError):
    """Surfaced when the per-account lockout (5 fails / 15 min → 10 min lock)
    has tripped (Story 1.5 §AC4).

    400 (not 423 HTTP Locked) is deliberate — returning 423 would tell the
    attacker "this account exists and we just locked it". The Problem
    Details `type`/`title`/`detail` ALL collapse to the wrong-password
    shape (`…/errors/validation` + "Validation" + same FR copy) so the
    lockout is indistinguishable from continued wrong-password attempts
    at every layer of the response body (code-review D1 — Story 1.5
    review 2026-05-27, resolved by collapsing the dedicated `type` URI).

    The unlock timestamp lives in the audit row + the DB column, NEVER
    in the response body.
    """

    type = "https://path-advisor.fr/errors/validation"
    title = "Validation"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Email ou mot de passe incorrect."


class AccountSuspended(AccountDeletionError):
    """Surfaced when a user with `status=SUSPENDED` attempts to log in.

    The 403 acknowledges the account exists but is unreachable. Detail is
    deliberately generic — does NOT reveal WHY suspension happened
    (parental-consent expiry, abuse flag, manual hold) so a moderator's
    decision can't be inferred from the login response (Story 1.5 §AC3).
    """

    type = "https://path-advisor.fr/errors/account-suspended"
    title = "Compte suspendu"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Ton compte est suspendu. Contacte le DPO si tu penses que c'est une erreur."


class EmailNotVerified(AccountDeletionError):
    """Surfaced when a user with `status=EMAIL_UNVERIFIED` attempts to log in.

    The `extras` payload carries the resend endpoint URL so the front can
    offer a one-click "renvoie-moi le mail" button without hard-coding the
    path (Story 1.5 §AC3). The hint is rendered as a TOP-LEVEL Problem
    Details extension (RFC 7807 §3.2) rather than under `body.errors` so
    a typed parser does not misclassify it as a field-level validation
    error (code-review P12 — Story 1.5 review 2026-05-27).
    """

    type = "https://path-advisor.fr/errors/email-not-verified"
    title = "Email non vérifié"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "Vérifie ton adresse email avant de te connecter. "
        "Si tu n'as pas reçu le mail, demande un nouvel envoi."
    )
    extras_as_extensions = True


# ---------------------------------------------------------------------------
# Story 1.6 — MFA (TOTP)
# ---------------------------------------------------------------------------


class MfaSessionExpired(AccountDeletionError):
    """Surfaced when the `mfa_session` token issued at password-success has
    expired (default TTL 5 min). The client must restart the login flow.
    """

    type = "https://path-advisor.fr/errors/mfa-session-expired"
    title = "Session MFA expirée"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Ta session de vérification a expiré. Reconnecte-toi pour relancer "
        "la double authentification."
    )
    extras_as_extensions = True


class MfaSessionConsumed(AccountDeletionError):
    """Surfaced when the `mfa_session` token was already used (successful
    challenge / enrollment-confirm completed, OR `MAX_FAILS_PER_TOKEN`
    failures blacklisted the JTI — code-review P15 + P28).

    Distinct from `MfaSessionInvalid` so the frontend can route to "your
    previous attempt already completed, reconnect" instead of the generic
    "tampered" message.
    """

    type = "https://path-advisor.fr/errors/mfa-session-consumed"
    title = "Session MFA déjà utilisée"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Cette session de vérification a déjà été utilisée. Reconnecte-toi "
        "pour en démarrer une nouvelle."
    )
    extras_as_extensions = True


class MfaSessionInvalid(AccountDeletionError):
    """Surfaced when the `mfa_session` token is malformed, signature-invalid,
    IP-mismatched, payload-malformed, OR for a wrong stage. Anti-enum: a
    single opaque error covers signature failure, IP mismatch, and wrong
    stage so attackers can't distinguish "tampered" from "wrong page".

    `MfaSessionExpired` and `MfaSessionConsumed` are SEPARATE so the UX
    can route to the right "what to do next" copy (code-review P15).
    """

    type = "https://path-advisor.fr/errors/mfa-session-invalid"
    title = "Session MFA invalide"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Session de vérification invalide. Reconnecte-toi."
    extras_as_extensions = True


class MfaChallengeFailed(AccountDeletionError):
    """Surfaced when the user submits an invalid TOTP / recovery code at the
    challenge or enrollment-confirm endpoint. Generic body — does NOT reveal
    whether the code was malformed, expired, or just wrong (anti-enum vs the
    user's whole code space).
    """

    type = "https://path-advisor.fr/errors/mfa-challenge-failed"
    title = "Code incorrect"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Code incorrect. Vérifie ton code et réessaie."
    extras_as_extensions = True


class MfaEnrollmentRequired(AccountDeletionError):
    """Surfaced when a user hits an MFA-protected endpoint (e.g. the
    challenge endpoint) without an enrolled device. The frontend should
    route them to the enrollment flow.
    """

    type = "https://path-advisor.fr/errors/mfa-enrollment-required"
    title = "Enrôlement MFA requis"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Tu dois enrôler une méthode MFA avant de continuer."
    extras_as_extensions = True


class MfaEnrollmentAlreadyComplete(AccountDeletionError):
    """Refuse `enroll/start/` for a user who is already enrolled (code-review
    P5). Without this, a stale `mfa_session` of stage `mfa_enrollment_pending`
    could create a 2nd unconfirmed device for an enrolled user, then a
    confirm flips it `confirmed=True` — leaving two confirmed devices.

    The DPO reset path is the only legitimate way to re-enroll an enrolled
    user (it sets `requires_enrollment_at_next_login=True`, which the view
    layer treats as a re-enrollment trigger).
    """

    type = "https://path-advisor.fr/errors/mfa-enrollment-already-complete"
    title = "MFA déjà enrôlée"
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "La MFA est déjà active sur ton compte. Pour changer d'authenticator, contacte le DPO."
    )
    extras_as_extensions = True


class MfaDisableForbiddenForStaff(AccountDeletionError):
    """Refuse the self-service disable for staff roles — NFR-S2 mandates
    MFA for `counselor`, `school_admin`, `path_admin`. The DPO override
    (`mfa.reset_by_dpo`) is the only way to clear MFA state for these roles.
    """

    type = "https://path-advisor.fr/errors/mfa-disable-forbidden"
    title = "Désactivation interdite"
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "La MFA est obligatoire pour ton rôle. Contacte le DPO si tu as "
        "perdu l'accès à ton authentificateur."
    )
    extras_as_extensions = True
