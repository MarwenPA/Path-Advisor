"""Service-layer tests for the account-deletion pipeline (Story 1.12)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.sessions.models import Session
from django.utils import timezone

from apps.accounts.gdpr_exceptions import (
    AccountDeletionAlreadyPending,
    AccountDeletionAlreadyResolved,
    AccountDeletionExpired,
    AccountDeletionNotFound,
    InvalidPassword,
)
from apps.accounts.models import (
    AccountDeletionRequest,
    User,
    UserStatus,
)
from apps.accounts.services import account_deletion as deletion_service
from apps.accounts.tests.factories import (
    PendingDeletionRequestFactory,
    UserFactory,
)
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


# ---------------------------------------------------------------------------
# request_deletion
# ---------------------------------------------------------------------------


def test_request_deletion_happy_path_soft_deletes_user_and_creates_row(mailoutbox):
    user = UserFactory(email="alice@example.test")

    deletion = deletion_service.request_deletion(user=user, password=_PWD)

    user.refresh_from_db()
    assert user.status == UserStatus.DELETED
    assert user.is_active is False
    assert user.deleted_at is not None

    assert deletion.user_id_snapshot == str(user.id)
    assert deletion.cancelled_at is None
    assert deletion.hard_deleted_at is None
    assert deletion.cancel_token  # non-empty
    assert deletion.hard_delete_after > timezone.now()

    # Confirmation email was sent
    assert any("demande de suppression" in (m.subject or "").lower() for m in mailoutbox)


def test_request_deletion_writes_audit_log_row():
    user = UserFactory()
    deletion_service.request_deletion(user=user, password=_PWD)

    row = AuditLog.objects.filter(action="gdpr.account_deletion_requested").first()
    assert row is not None
    assert row.subject_id == str(user.id)
    assert row.metadata.get("deletion_request_id")


def test_request_deletion_invalid_password_raises_400():
    user = UserFactory()
    with pytest.raises(InvalidPassword):
        deletion_service.request_deletion(user=user, password="wrong")

    user.refresh_from_db()
    # No state change on failure.
    assert user.status == UserStatus.ACTIVE
    assert not AccountDeletionRequest.objects.exists()


def test_request_deletion_already_pending_raises_409():
    user = UserFactory()
    deletion_service.request_deletion(user=user, password=_PWD)

    with pytest.raises(AccountDeletionAlreadyPending):
        # Even with the right password — only one in-flight request per user.
        deletion_service.request_deletion(user=user, password=_PWD)


def test_request_deletion_terminates_active_sessions(client, settings):
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
    user = UserFactory()
    # Story 1.12 code review §P19: use the canonical `SessionStore` API
    # (instance method) instead of the deprecated `Session.objects.encode(...)`
    # which doesn't exist on the queryset manager in modern Django. This
    # actually exercises the same encoding path the production session
    # middleware uses, so the test validates the real `_terminate_user_sessions`
    # decode path.
    from django.contrib.sessions.backends.db import SessionStore

    store = SessionStore()
    store["_auth_user_id"] = str(user.id)
    store.create()  # Persists with a real session_key + encoded payload.
    assert Session.objects.count() == 1

    deletion_service.request_deletion(user=user, password=_PWD)

    assert Session.objects.count() == 0


def test_request_deletion_smtp_failure_rolls_back():
    user = UserFactory()
    # Patch the send fn to raise — atomicity contract says everything reverts.
    with (
        patch(
            "apps.accounts.services.account_deletion_email.send_account_deletion_requested_email",
            side_effect=RuntimeError("smtp boom"),
        ),
        pytest.raises(RuntimeError),
    ):
        deletion_service.request_deletion(user=user, password=_PWD)

    user.refresh_from_db()
    assert user.status == UserStatus.ACTIVE  # NOT deleted
    assert user.is_active is True
    assert not AccountDeletionRequest.objects.exists()


# ---------------------------------------------------------------------------
# cancel_deletion
# ---------------------------------------------------------------------------


def test_cancel_deletion_restores_user_and_marks_row(mailoutbox):
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    user.refresh_from_db()
    assert user.status == UserStatus.DELETED

    restored = deletion_service.cancel_deletion(
        request=deletion,
        password=_PWD,
        cancel_reason="user_self_service",
    )

    user.refresh_from_db()
    assert user.status == UserStatus.ACTIVE
    assert user.is_active is True
    assert user.deleted_at is None

    assert restored.cancelled_at is not None
    assert restored.cancel_reason == "user_self_service"

    # Restoration email
    assert any("restauré" in (m.subject or "").lower() for m in mailoutbox)


def test_cancel_deletion_wrong_password_raises_400():
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)

    with pytest.raises(InvalidPassword):
        deletion_service.cancel_deletion(request=deletion, password="wrong")


def test_cancel_deletion_already_cancelled_raises_409():
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    deletion_service.cancel_deletion(request=deletion, password=_PWD)
    deletion.refresh_from_db()

    with pytest.raises(AccountDeletionAlreadyResolved):
        deletion_service.cancel_deletion(request=deletion, password=_PWD)


def test_cancel_deletion_past_grace_window_raises_410():
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        hard_delete_after=timezone.now() - timedelta(hours=1),
    )

    with pytest.raises(AccountDeletionExpired):
        deletion_service.cancel_deletion(request=deletion, password=_PWD)


def test_cancel_deletion_dpo_override_skips_password():
    """When `password=None` and `actor` is provided, skip the password check."""
    dpo = UserFactory()
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)

    restored = deletion_service.cancel_deletion(
        request=deletion,
        password=None,
        actor=dpo,
        cancel_reason=f"dpo_override:{dpo.id}:identity verified",
    )

    user.refresh_from_db()
    assert user.status == UserStatus.ACTIVE
    assert restored.cancel_reason.startswith("dpo_override:")


def test_cancel_deletion_no_password_no_actor_refused():
    """Defensive: bypassing the password without an admin actor must fail."""
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)

    with pytest.raises(InvalidPassword):
        deletion_service.cancel_deletion(request=deletion, password=None, actor=None)


# ---------------------------------------------------------------------------
# lookup_request_by_token
# ---------------------------------------------------------------------------


def test_lookup_request_by_token_returns_row():
    deletion = PendingDeletionRequestFactory()
    found = deletion_service.lookup_request_by_token(deletion.cancel_token)
    assert found.pk == deletion.pk


def test_lookup_request_by_token_unknown_raises_404():
    PendingDeletionRequestFactory()
    with pytest.raises(AccountDeletionNotFound):
        deletion_service.lookup_request_by_token("does-not-exist-token")


# ---------------------------------------------------------------------------
# hard_delete — the legal core
# ---------------------------------------------------------------------------


def test_hard_delete_wipes_user_row_and_writes_audit():
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    user_id = user.id

    # Move past the grace window
    deletion.hard_delete_after = timezone.now() - timedelta(seconds=1)
    deletion.save(update_fields=["hard_delete_after"])

    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        return_value=(0, []),
    ):
        result = deletion_service.hard_delete(deletion)

    assert not User.objects.filter(pk=user_id).exists()
    deletion.refresh_from_db()
    assert deletion.hard_deleted_at is not None

    # Audit row survives the cascade because subject_id is a CharField, not a FK.
    assert AuditLog.objects.filter(
        action="gdpr.account_hard_deleted",
        subject_id=user_id,
    ).exists()
    assert result["user_id"] == user_id


def test_hard_delete_is_idempotent():
    """A re-run on a row already hard-deleted must not double-audit or crash."""
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    deletion.hard_delete_after = timezone.now() - timedelta(seconds=1)
    deletion.save(update_fields=["hard_delete_after"])

    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        return_value=(0, []),
    ):
        deletion_service.hard_delete(deletion)
        # Second call must be a no-op.
        result = deletion_service.hard_delete(deletion)

    assert result.get("skipped") == "already_hard_deleted"
    # Exactly one hard-delete audit row.
    assert AuditLog.objects.filter(action="gdpr.account_hard_deleted").count() == 1


def test_hard_delete_skips_cancelled_row():
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    deletion_service.cancel_deletion(request=deletion, password=_PWD)
    deletion.refresh_from_db()
    deletion.hard_delete_after = timezone.now() - timedelta(seconds=1)
    deletion.save(update_fields=["hard_delete_after"])

    result = deletion_service.hard_delete(deletion)
    assert result.get("skipped") == "cancelled"

    # User still exists.
    assert User.objects.filter(pk=user.id).exists()


def test_hard_delete_writes_audit_before_user_cascade():
    """The audit row's subject_id MUST be the user id, written before the cascade."""
    user = UserFactory()
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    deletion.hard_delete_after = timezone.now() - timedelta(seconds=1)
    deletion.save(update_fields=["hard_delete_after"])

    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        return_value=(0, []),
    ):
        deletion_service.hard_delete(deletion)

    row = AuditLog.objects.filter(action="gdpr.account_hard_deleted").first()
    assert row is not None
    assert row.subject_id == user.id  # captured before the cascade
    # User is gone now.
    assert not User.objects.filter(pk=user.id).exists()
