"""Student-import-invitation accept service — Story 6.5 §T2.5 (AC5).

Same email-locking contract as `services.counselor_invitation` (§4.4):
`invitation.user.email` is never overridden by a body-supplied field — there
is in fact no email field at all on this accept endpoint (the user already
exists, created by the CSV import job), only `password`.
"""

from __future__ import annotations

import secrets

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, UserStatus
from apps.audit.decorators import audit_action
from apps.establishments.exceptions import InvitationNotFoundOrExpired
from apps.establishments.models import StudentImportInvitation, StudentImportInvitationStatus

_TOKEN_BYTES = 32


def generate_token() -> str:
    return secrets.token_urlsafe(_TOKEN_BYTES)


def get_invitation_by_token(token: str) -> StudentImportInvitation:
    invitation = (
        StudentImportInvitation.objects.filter(token=token).select_related("user", "cohort").first()
    )
    if invitation is None:
        raise InvitationNotFoundOrExpired()
    return invitation


@audit_action(
    "student_import_invitation.accepted",
    subject_from=lambda kwargs, ret: kwargs["invitation"].user_id,
    metadata_from=lambda kwargs, ret: {
        "invitation_id": kwargs["invitation"].id,
        "status": ret.status,
    },
)
def accept_invitation(*, invitation: StudentImportInvitation, password: str) -> User:
    """AC5 — the student picks their own password. Distinct terminal states:

    - `email_unverified` (≥15 y/o) → `active` + `email_verified_at=now` (the
      link click acts as email verification — no double confirmation email).
    - `pending_parental_consent` (<15 y/o) → password saved but status is
      LEFT UNCHANGED; the parent's decision (Story 1.4) is the only thing
      that can move it forward.
    """
    now = timezone.now()
    if invitation.status != StudentImportInvitationStatus.PENDING or invitation.is_expired:
        raise InvitationNotFoundOrExpired()

    validate_password(password)

    with transaction.atomic():
        locked = StudentImportInvitation.objects.select_for_update().get(pk=invitation.pk)
        if locked.status != StudentImportInvitationStatus.PENDING or locked.is_expired:
            raise InvitationNotFoundOrExpired()

        student = User.objects.select_for_update().get(pk=locked.user_id)
        student.set_password(password)
        update_fields = ["password"]
        if student.status == UserStatus.EMAIL_UNVERIFIED:
            student.status = UserStatus.ACTIVE
            student.email_verified_at = now
            update_fields += ["status", "email_verified_at"]
        # else: pending_parental_consent stays as-is (AC5 last clause).
        student.save(update_fields=update_fields)

        locked.status = StudentImportInvitationStatus.ACCEPTED
        locked.accepted_at = now
        locked.save(update_fields=["status", "accepted_at"])

    return student
