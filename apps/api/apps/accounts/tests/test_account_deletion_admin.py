"""Django admin DPO override tests (Story 1.12 §AC9)."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.accounts.models import UserStatus
from apps.accounts.tests.factories import PendingDeletionRequestFactory, UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


def _grant_dpo_perm(user) -> None:
    perm = Permission.objects.get(codename="cancel_deletion_request")
    user.user_permissions.add(perm)
    # Re-fetch so the new permissions cache is hot for the test.
    return type(user).objects.get(pk=user.pk)


def test_dpo_cancel_action_restores_account_and_writes_audit(client):
    dpo = UserFactory(is_staff=True, is_superuser=True)
    _grant_dpo_perm(dpo)
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
    )
    user.status = UserStatus.DELETED
    user.is_active = False
    user.save(update_fields=["status", "is_active"])

    client.force_login(dpo)
    url = reverse(
        "admin:accounts_accountdeletionrequest_dpo_cancel",
        args=[deletion.pk],
    )
    res = client.post(url, {"cancel_reason": "support callback 2026-05-30 — verified id"})
    assert res.status_code == 302  # redirect back to changelist

    deletion.refresh_from_db()
    user.refresh_from_db()
    assert deletion.cancelled_at is not None
    assert deletion.cancel_reason.startswith(f"dpo_override:{dpo.id}:")
    assert user.status == UserStatus.ACTIVE

    audit = AuditLog.objects.filter(action="gdpr.account_deletion_cancelled").first()
    assert audit is not None
    assert audit.metadata.get("via") == "dpo_override"


def test_dpo_cancel_refused_without_permission(client):
    # Staff WITHOUT is_superuser AND without the explicit cancel_deletion_request perm.
    # (Django superusers bypass has_perm checks — that's the intended grant path.)
    staff_only = UserFactory(is_staff=True, is_superuser=False)
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
    )

    client.force_login(staff_only)
    url = reverse(
        "admin:accounts_accountdeletionrequest_dpo_cancel",
        args=[deletion.pk],
    )
    res = client.post(url, {"cancel_reason": "test"})
    # Redirect to changelist with an error message — NOT cancelled.
    assert res.status_code == 302
    deletion.refresh_from_db()
    assert deletion.cancelled_at is None


def test_dpo_cancel_refused_for_superuser_without_explicit_perm(client):
    """Story 1.12 §D1: `is_superuser=True` alone is NOT sufficient to perform
    the DPO override. The strict permission check (`_has_explicit_dpo_perm`)
    bypasses Django's superuser shortcut on `has_perm`.
    """
    # Superuser without the explicit `cancel_deletion_request` permission.
    superuser_only = UserFactory(is_staff=True, is_superuser=True)
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
    )

    client.force_login(superuser_only)
    url = reverse(
        "admin:accounts_accountdeletionrequest_dpo_cancel",
        args=[deletion.pk],
    )
    res = client.post(url, {"cancel_reason": "test"})
    # Redirect with an error message — NOT cancelled.
    assert res.status_code == 302
    deletion.refresh_from_db()
    assert deletion.cancelled_at is None


def test_dpo_cancel_requires_reason(client):
    dpo = UserFactory(is_staff=True, is_superuser=True)
    _grant_dpo_perm(dpo)
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
    )

    client.force_login(dpo)
    url = reverse(
        "admin:accounts_accountdeletionrequest_dpo_cancel",
        args=[deletion.pk],
    )
    res = client.post(url, {"cancel_reason": ""})
    assert res.status_code == 200  # re-renders the form with errors
    deletion.refresh_from_db()
    assert deletion.cancelled_at is None
