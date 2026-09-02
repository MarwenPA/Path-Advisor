"""Counselor-invitation service — Story 6.5 §T2.3 (AC4).

Pattern copied from `apps.family.services.parent_invitation`. §4.4
anti-pattern guard (Story 6.1 review): `accept_invitation` uses EXCLUSIVELY
`invitation.email` to create the account — the `password` is the only value
ever taken from the request body.
"""

from __future__ import annotations

import hashlib
import secrets

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.decorators import audit_action
from apps.establishments.exceptions import InvitationNotFoundOrExpired
from apps.establishments.models import CounselorInvitation, CounselorInvitationStatus, Establishment

_TOKEN_BYTES = 32


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(_TOKEN_BYTES)


def _enqueue_send_invitation(invitation_id: str) -> None:
    from apps.establishments.tasks import send_counselor_invitation_email

    send_counselor_invitation_email.delay(invitation_id)


@audit_action(
    "counselor_invitation.created",
    subject_from=lambda kwargs, ret: str(kwargs["establishment"].id),
    metadata_from=lambda kwargs, ret: {
        "invitation_id": ret.id,
        "email_hash": sha256_hex(kwargs["email"]),
    },
)
def create_counselor_invitation(*, establishment: Establishment, email: str) -> CounselorInvitation:
    """AC4 — create a `pending` invitation + enqueue the email."""
    with transaction.atomic():
        invitation = CounselorInvitation.objects.create(
            establishment=establishment,
            email=email,
            token=_generate_token(),
        )
        transaction.on_commit(lambda: _enqueue_send_invitation(invitation.id))
    return invitation


def get_invitation_by_token(token: str) -> CounselorInvitation:
    invitation = (
        CounselorInvitation.objects.filter(token=token).select_related("establishment").first()
    )
    if invitation is None:
        raise InvitationNotFoundOrExpired()
    return invitation


@audit_action(
    "counselor_invitation.accepted",
    subject_from=lambda kwargs, ret: str(kwargs["invitation"].establishment_id),
    metadata_from=lambda kwargs, ret: {
        "invitation_id": kwargs["invitation"].id,
        "establishment_id": str(kwargs["invitation"].establishment_id),
    },
)
def accept_invitation(*, invitation: CounselorInvitation, password: str) -> User:
    """AC4 — accept: create `User(role=counselor)`.

    Security (§4.4 / Story 6.1 review lesson): the account email is ALWAYS
    `invitation.email` — never a body-supplied field. A token that is not
    `pending` or is expired is reported as `InvitationNotFoundOrExpired`
    (404), never distinguishing "expired" from "unknown" (anti-enumeration).

    Password is always required + validated — never `required=False`.
    """
    now = timezone.now()
    if invitation.status != CounselorInvitationStatus.PENDING or invitation.is_expired:
        raise InvitationNotFoundOrExpired()

    validate_password(password)

    with transaction.atomic():
        # Re-check under lock to avoid a double-accept race creating two accounts.
        locked = CounselorInvitation.objects.select_for_update().get(pk=invitation.pk)
        if locked.status != CounselorInvitationStatus.PENDING or locked.is_expired:
            raise InvitationNotFoundOrExpired()

        counselor = User.objects.create_user(
            email=locked.email,
            password=password,
            role=UserRole.COUNSELOR,
            status=UserStatus.ACTIVE,
            email_verified_at=now,
            tenant_id=locked.establishment_id,
        )

        locked.status = CounselorInvitationStatus.ACCEPTED
        locked.accepted_at = now
        locked.save(update_fields=["status", "accepted_at"])

    return counselor
