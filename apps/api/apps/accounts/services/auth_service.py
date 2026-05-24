"""Business logic for account creation and email verification (Story 1.3 + 1.13)."""

from __future__ import annotations

import structlog
from django.utils import timezone

from apps.accounts.models import User, UserStatus
from apps.audit.decorators import audit_action

log = structlog.get_logger(__name__)


@audit_action(
    "user.email_verified",
    subject_from=lambda kwargs, ret: ret.id,
    metadata_from=lambda kwargs, ret: {"role": ret.role, "status_after": ret.status},
)
def mark_email_verified(user: User) -> User:
    """Activate a user account after they click the verification link.

    Called from `apps.accounts.signals` listening on allauth's
    `email_confirmed` signal. Idempotent: safe to call multiple times.

    State machine (Story 1.4 §AC3): for minors in `pending_parental_consent` we
    only stamp `email_verified_at`; status stays pending until the parent grants
    (handled by `parental_consent.record_decision`). Without this guard the
    child can bypass the parental gate by verifying email first — the entire
    legal opt-in is moot.
    """
    if user.status == UserStatus.ACTIVE and user.email_verified_at is not None:
        log.info(
            "user.email_verified.skipped",
            actor_id=user.id,
            reason="already_active",
        )
        return user

    user.email_verified_at = timezone.now()

    if user.status == UserStatus.PENDING_PARENTAL_CONSENT:
        # Check whether parental consent has already been granted; if so, both
        # gates are now passed and the user can transition to ACTIVE.
        from apps.accounts.models import ParentalConsent, ParentalConsentDecision

        has_granted = ParentalConsent.objects.filter(
            student=user,
            decision=ParentalConsentDecision.GRANTED,
        ).exists()
        if has_granted:
            user.status = UserStatus.ACTIVE
            update_fields = ["email_verified_at", "status", "updated_at"]
        else:
            # Stay pending — parent must still decide. Story 1.4 §AC3 row 1.
            update_fields = ["email_verified_at", "updated_at"]
    else:
        # Story 1.3 happy path: ≥ 15 ans goes straight from EMAIL_UNVERIFIED to ACTIVE.
        user.status = UserStatus.ACTIVE
        update_fields = ["email_verified_at", "status", "updated_at"]

    user.save(update_fields=update_fields)

    log.info(
        "user.email_verified",
        actor_id=user.id,
        role=user.role,
        status_after=user.status,
        verified_at=user.email_verified_at.isoformat(),
    )
    return user


@audit_action(
    "user.signed_up",
    subject_from=lambda kwargs, ret: kwargs["user"].id,
    metadata_from=lambda kwargs, ret: {
        "role": kwargs["user"].role,
        "status": kwargs["user"].status,
        "consent_cgu_version": kwargs["user"].consent_cgu_version or "",
    },
)
def record_signup_event(*, user: User) -> None:
    """Persist the signup event in the audit log AND emit operational structlog."""
    log.info(
        "user.signed_up",
        actor_id=user.id,
        role=user.role,
        status=user.status,
        consent_cgu_version=user.consent_cgu_version,
    )


def log_signup(user: User) -> None:
    """Backwards-compatible wrapper kept so callers still using the old name work.

    Prefer `record_signup_event(user=user)` for new code; this delegates to it.
    """
    record_signup_event(user=user)
