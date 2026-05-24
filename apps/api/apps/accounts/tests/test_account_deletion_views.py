"""HTTP-level tests for the account-deletion endpoints (Story 1.12)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AccountDeletionRequest, UserStatus
from apps.accounts.tests.factories import PendingDeletionRequestFactory, UserFactory

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"
# Story 1.12 §D2 follow-up: every POST to the request endpoint carries the
# ConsentDialog forensic fields. Tests share a fixed `content_hash` (any
# 64-hex string works for the serializer regex) + a frozen `accepted_at`.
_CONTENT_HASH = "0" * 64
_ACCEPTED_AT = "2026-05-25T10:00:00Z"


@pytest.fixture(autouse=True)
def _clear_ratelimit_cache():
    """Story 1.12: the deletion endpoint is rate-limited at 3/24h per IP.
    Reset the in-memory cache between tests so per-test cases don't leak
    counters into each other (mirrors the test_signup.py fixture).
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def _request_payload(password: str = _PWD) -> dict:
    return {
        "password": password,
        "content_hash": _CONTENT_HASH,
        "accepted_at": _ACCEPTED_AT,
    }


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authed_user_and_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user)
    return user, api_client


# ---------------------------------------------------------------------------
# POST /api/v1/auth/me/account-deletion/  (AC1)
# ---------------------------------------------------------------------------


def test_post_account_deletion_happy_path(authed_user_and_client):
    user, client = authed_user_and_client
    url = reverse("accounts:account-deletion-request")
    res = client.post(url, _request_payload(), format="json")
    assert res.status_code == 202, res.content
    user.refresh_from_db()
    assert user.status == UserStatus.DELETED
    assert AccountDeletionRequest.objects.filter(user_id_snapshot=str(user.id)).count() == 1
    # AC1 response shape (P18): exposes status + detail + lifecycle dates.
    body = res.json()
    assert body["status"] == "pending_hard_delete"
    assert "30 jours" in body["detail"]


def test_post_account_deletion_invalid_password_400(authed_user_and_client):
    _, client = authed_user_and_client
    res = client.post(
        reverse("accounts:account-deletion-request"),
        _request_payload(password="wrong"),
        format="json",
    )
    assert res.status_code == 400
    assert "invalid-password" in res.json()["type"]


def test_post_account_deletion_already_pending_409(authed_user_and_client):
    user, client = authed_user_and_client
    PendingDeletionRequestFactory(user=user, user_id_snapshot=str(user.id))
    user.status = UserStatus.DELETED
    user.is_active = False
    user.save(update_fields=["status", "is_active"])
    # User is DELETED so they can't even reach this endpoint via session-cookie auth,
    # but force_authenticate bypasses that. The service still catches the duplicate.
    client.force_authenticate(user)

    res = client.post(
        reverse("accounts:account-deletion-request"),
        _request_payload(),
        format="json",
    )
    assert res.status_code == 409


def test_post_account_deletion_forwards_content_hash_to_audit_metadata(
    authed_user_and_client,
):
    """Story 1.12 §D2: ConsentDialog's `contentHash` + `acceptedAt` are
    preserved in the audit row metadata so the audit log carries the FR12
    immutability proof of what the user saw at decision time.
    """
    from apps.audit.models import AuditLog

    _user, client = authed_user_and_client
    url = reverse("accounts:account-deletion-request")
    res = client.post(url, _request_payload(), format="json")
    assert res.status_code == 202

    row = AuditLog.objects.filter(action="gdpr.account_deletion_requested").first()
    assert row is not None
    assert row.metadata.get("content_hash") == _CONTENT_HASH
    # accepted_at is normalised to ISO 8601 — just assert presence + parseability.
    assert row.metadata.get("accepted_at", "").startswith("2026-")


def test_post_account_deletion_rejects_invalid_content_hash(authed_user_and_client):
    """Spec validates the content_hash format (lowercase 64-hex SHA-256)."""
    _, client = authed_user_and_client
    payload = _request_payload()
    payload["content_hash"] = "not-a-hash"
    res = client.post(
        reverse("accounts:account-deletion-request"),
        payload,
        format="json",
    )
    assert res.status_code == 400


def test_post_account_deletion_unauthenticated_401(api_client):
    res = api_client.post(
        reverse("accounts:account-deletion-request"),
        _request_payload(),
        format="json",
    )
    # Story 1.12 code review §P20: DRF SessionAuthentication without creds
    # returns 401 + the typed `not-authenticated` Problem Details (cf.
    # `apps/core/exceptions.py:NotAuthenticated` handler at line 191-202).
    # Pin to the actual contract instead of accepting both 401 + 403.
    assert res.status_code == 401
    assert "not-authenticated" in res.json()["type"]


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me/account-deletion/status/
# ---------------------------------------------------------------------------


def test_get_my_status_returns_pending_row(authed_user_and_client):
    user, client = authed_user_and_client
    deletion = PendingDeletionRequestFactory(user=user, user_id_snapshot=str(user.id))

    res = client.get(reverse("accounts:account-deletion-status-self"))
    assert res.status_code == 200
    assert res.json()["id"] == deletion.id


def test_get_my_status_returns_404_when_none(authed_user_and_client):
    _, client = authed_user_and_client
    res = client.get(reverse("accounts:account-deletion-status-self"))
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/auth/account-deletion/<token>/  (AC5 — public)
# ---------------------------------------------------------------------------


def test_get_public_status_returns_masked_email(api_client):
    user = UserFactory(email="alice@example.test")
    deletion = PendingDeletionRequestFactory(user=user, user_id_snapshot=str(user.id))

    res = api_client.get(
        reverse("accounts:account-deletion-status-public", args=[deletion.cancel_token])
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "pending_hard_delete"
    # Email is masked
    assert "alice@example.test" not in body["user_email_masked"]
    assert "@" in body["user_email_masked"]


def test_get_public_status_unknown_token_404(api_client):
    res = api_client.get(reverse("accounts:account-deletion-status-public", args=["nope-token"]))
    assert res.status_code == 404


def test_get_public_status_returns_404_for_cancelled_row(api_client):
    """Story 1.12 §D3 — anti-enumeration: terminal states must not leak
    deletion lifecycle to anyone holding the token.
    """
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        cancelled_at=timezone.now(),
    )
    res = api_client.get(
        reverse("accounts:account-deletion-status-public", args=[deletion.cancel_token])
    )
    assert res.status_code == 404


def test_get_public_status_returns_404_for_expired_row(api_client):
    """Story 1.12 §D3 — terminal state (past grace window) returns 404."""
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() - timedelta(hours=1),
    )
    res = api_client.get(
        reverse("accounts:account-deletion-status-public", args=[deletion.cancel_token])
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/auth/account-deletion/<token>/cancel/  (AC5)
# ---------------------------------------------------------------------------


def test_post_cancel_restores_user(api_client):
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(user=user, user_id_snapshot=str(user.id))
    user.status = UserStatus.DELETED
    user.is_active = False
    user.save(update_fields=["status", "is_active"])

    res = api_client.post(
        reverse("accounts:account-deletion-cancel", args=[deletion.cancel_token]),
        {"password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    user.refresh_from_db()
    assert user.status == UserStatus.ACTIVE
    deletion.refresh_from_db()
    assert deletion.cancelled_at is not None


def test_post_cancel_wrong_password_400(api_client):
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(user=user, user_id_snapshot=str(user.id))
    res = api_client.post(
        reverse("accounts:account-deletion-cancel", args=[deletion.cancel_token]),
        {"password": "wrong"},
        format="json",
    )
    assert res.status_code == 400


def test_post_cancel_expired_window_410(api_client):
    user = UserFactory()
    deletion = PendingDeletionRequestFactory(
        user=user,
        user_id_snapshot=str(user.id),
        hard_delete_after=timezone.now() - timedelta(hours=1),
    )
    res = api_client.post(
        reverse("accounts:account-deletion-cancel", args=[deletion.cancel_token]),
        {"password": _PWD},
        format="json",
    )
    assert res.status_code == 410


def test_post_cancel_unknown_token_404(api_client):
    res = api_client.post(
        reverse("accounts:account-deletion-cancel", args=["nope-token"]),
        {"password": _PWD},
        format="json",
    )
    assert res.status_code == 404
