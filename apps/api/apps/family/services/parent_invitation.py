"""Parent-invitation service — Story 6.1 §T2.

Owns every write to `ParentInvitation` / `ParentStudentLink`. Views must never
touch the models directly — every state transition produces exactly one
`AuditLog` row via `@audit_action` (Story 1.13), same contract as
`apps.accounts.services.parental_consent`.

The token generation / TTL / rate-limit conventions are copy-pasted from the
Story 1.4 pattern (`secrets.token_urlsafe(32)`).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.audit.decorators import audit_action
from apps.family.exceptions import (
    ParentInvitationAlreadyPending,
    ParentInvitationEmailTaken,
    ParentInvitationNotFoundOrExpired,
    ParentInvitationResendRateLimited,
)
from apps.family.models import ParentInvitation, ParentInvitationStatus, ParentStudentLink

_TOKEN_BYTES = 32
_INVITATION_TTL_DAYS = 30
_RESEND_RATE_LIMIT_SECONDS = 3600


def sha256_hex(value: str) -> str:
    """Lowercase SHA-256 hex — used for `parent_email_hash` in audit metadata
    (Story 1.4 §AC4 pattern — never store the plain parent email in audit rows).
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(_TOKEN_BYTES)


@audit_action(
    "parent_invitation.created",
    subject_from=lambda kwargs, ret: kwargs["student"].id,
    metadata_from=lambda kwargs, ret: {
        "parent_email_hash": sha256_hex(kwargs["parent_email"]),
        "invitation_id": ret.id,
        "relationship": kwargs.get("relationship"),
    },
)
def create_invitation(
    *,
    student: User,
    parent_email: str,
    relationship: str | None = None,
    custom_message: str | None = None,
) -> ParentInvitation:
    """AC1 / AC2 — create a `pending` invitation.

    Raises `ParentInvitationAlreadyPending` (409) if a non-expired `pending`
    invitation already exists towards the same email for this student.

    Story 4.4 anti-pattern note: the élève's account status
    (`pending_parental_consent` etc.) is deliberately NOT checked here — the
    invitation flow is independent of the inviter's own account state
    (cf. story §4.4 last bullet).
    """
    now = timezone.now()
    existing = ParentInvitation.objects.filter(
        student=student,
        parent_email__iexact=parent_email,
        status=ParentInvitationStatus.PENDING,
        expires_at__gt=now,
    ).first()
    if existing is not None:
        raise ParentInvitationAlreadyPending()

    with transaction.atomic():
        invitation = ParentInvitation.objects.create(
            student=student,
            parent_email=parent_email,
            relationship=relationship,
            custom_message=custom_message,
            token=_generate_token(),
            created_at=now,
            expires_at=now + timedelta(days=_INVITATION_TTL_DAYS),
        )
        transaction.on_commit(lambda: _enqueue_send_invitation(invitation.id))
    return invitation


def _enqueue_send_invitation(invitation_id: str) -> None:
    from apps.family.tasks import send_parent_invitation_email

    send_parent_invitation_email.delay(invitation_id)


def _enqueue_send_accepted(invitation_id: str, parent_id: str) -> None:
    from apps.family.tasks import send_parent_invitation_accepted_email

    send_parent_invitation_accepted_email.delay(invitation_id, parent_id)


def get_invitation_by_token(token: str) -> ParentInvitation:
    """AC3 — public read. Raises 404-mapped error if absent/expired/non-pending
    is NOT enforced here (the view needs the row even in a terminal state to
    render "no longer valid") — `get_invitation_by_token` only 404s on a
    genuinely unknown token; state validity is checked by the caller.
    """
    invitation = ParentInvitation.objects.filter(token=token).select_related("student").first()
    if invitation is None:
        raise ParentInvitationNotFoundOrExpired()
    return invitation


def _rate_limit_key(invitation_id: str) -> str:
    return f"family:parent_invitation:resend:{invitation_id}"


@audit_action(
    "parent_invitation.resent",
    subject_from=lambda kwargs, ret: kwargs["invitation"].student_id,
    metadata_from=lambda kwargs, ret: {
        "invitation_id": kwargs["invitation"].id,
        "parent_email_hash": sha256_hex(kwargs["invitation"].parent_email),
    },
)
def resend_invitation(*, invitation: ParentInvitation) -> ParentInvitation:
    """T2.4 — rate-limited 1/hour/invitation. Reuses the existing token if
    still valid (AC2 second clause).
    """
    key = _rate_limit_key(invitation.id)
    if cache.get(key):
        raise ParentInvitationResendRateLimited()
    cache.set(key, True, timeout=_RESEND_RATE_LIMIT_SECONDS)
    transaction.on_commit(lambda: _enqueue_send_invitation(invitation.id))
    return invitation


@audit_action(
    "parent_invitation.accepted",
    # actor_id stays NULL (anonymous acceptance path) unless resolved by
    # `request_context` for an already-authenticated parent (AC4 second case).
    subject_from=lambda kwargs, ret: kwargs["invitation"].student_id,
    metadata_from=lambda kwargs, ret: {
        "parent_email_hash": sha256_hex(kwargs["invitation"].parent_email),
        "relationship": kwargs["invitation"].relationship,
        "invitation_id": kwargs["invitation"].id,
    },
)
def accept_invitation(
    *,
    invitation: ParentInvitation,
    existing_user: User | None = None,
    email: str | None = None,
    password: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    # NOTE (Story 6.1 scope decision): `apps.accounts.models.User` has no
    # `first_name`/`last_name` fields today (checked before writing this
    # service — grep found none anywhere in the codebase). Adding them is a
    # cross-cutting `accounts` migration outside this story's scope; the
    # frontend still collects nom/prénom per AC3 but they are only used for
    # display purposes client-side today. Documented as a known gap in the
    # story's Completion Notes / deferred-work.md candidate.
    """AC3 / AC4 — accept an invitation, either anonymously (creates a new
    `User(role="parent")`) or for an already-authenticated `role="parent"` user
    (adds a second `ParentStudentLink`, no account created).

    Raises `ParentInvitationNotFoundOrExpired` if the invitation is not
    `pending` or has expired. Raises `ParentInvitationEmailTaken` (409) if the
    anonymous path targets an email already owned by another `User`.
    """
    now = timezone.now()
    if invitation.status != ParentInvitationStatus.PENDING or invitation.is_expired:
        raise ParentInvitationNotFoundOrExpired()

    with transaction.atomic():
        if existing_user is not None:
            parent_user = existing_user
        else:
            target_email = email or invitation.parent_email
            if User.objects.filter(email__iexact=target_email).exists():
                raise ParentInvitationEmailTaken()
            from apps.accounts.models import UserStatus

            parent_user = User.objects.create_user(
                email=target_email,
                password=password,
                role=UserRole.PARENT,
                status=UserStatus.ACTIVE,
                email_verified_at=now,
                consent_rgpd_at=now,
            )

        ParentStudentLink.objects.get_or_create(
            parent=parent_user,
            student=invitation.student,
            revoked_at=None,
            defaults={"relationship": invitation.relationship},
        )

        invitation.status = ParentInvitationStatus.ACCEPTED
        invitation.accepted_at = now
        invitation.save(update_fields=["status", "accepted_at", "updated_at"])

        transaction.on_commit(lambda: _enqueue_send_accepted(invitation.id, parent_user.id))

    return parent_user
