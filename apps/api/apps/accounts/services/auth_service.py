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
    metadata_from=lambda kwargs, ret: {"role": ret.role},
)
def mark_email_verified(user: User) -> User:
    """Activate a user account after they click the verification link.

    Called from `apps.accounts.signals` listening on allauth's
    `email_confirmed` signal. Idempotent: safe to call multiple times.
    """
    if user.status == UserStatus.ACTIVE and user.email_verified_at is not None:
        log.info(
            "user.email_verified.skipped",
            actor_id=user.id,
            reason="already_active",
        )
        return user

    user.email_verified_at = timezone.now()
    user.status = UserStatus.ACTIVE
    user.save(update_fields=["email_verified_at", "status", "updated_at"])

    log.info(
        "user.email_verified",
        actor_id=user.id,
        role=user.role,
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
