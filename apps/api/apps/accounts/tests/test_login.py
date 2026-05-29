"""Login endpoint tests — Story 1.5 §AC1, §AC2, §AC3, §AC9.

Covers happy path, generic-error wrong password, status-aware rejections
(SUSPENDED / EMAIL_UNVERIFIED — DELETED already covered by Story 1.12's
test_login_serializer_delete.py), and audit-row writes.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.accounts.tests.factories import EmailUnverifiedUserFactory, UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


def _make_active_user(email: str = "alice@example.test"):
    """Create a User + the allauth `EmailAddress` row that login validates.

    `UserFactory` only sets `User.email_verified_at`. allauth checks its
    own `EmailAddress` table for verification status, so a UserFactory
    user can't actually log in unless we seed that row too.
    """
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email)
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    return user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def test_login_happy_path_returns_200_with_user_payload(api_client):
    _make_active_user("alice@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    # dj-rest-auth wraps user details in a `user` key when SESSION_LOGIN=True.
    body = res.json()
    assert "user" in body
    assert body["user"]["email"] == "alice@example.test"
    assert body["user"]["role"] == "student"
    assert body["user"]["status"] == "active"


def test_login_success_writes_audit_row(api_client):
    user = _make_active_user("alice@example.test")
    api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": _PWD},
        format="json",
    )
    row = AuditLog.objects.filter(action="auth.login_succeeded").first()
    assert row is not None
    assert row.subject_id == user.id
    # email_hashed should be a 64-char sha256 hex
    assert len(row.metadata.get("email_hashed", "")) == 64


_GENERIC_VALIDATION_TYPE = "https://path-advisor.fr/errors/validation"


def test_login_wrong_password_returns_400_generic(api_client):
    _make_active_user("alice@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": "wrong"},
        format="json",
    )
    assert res.status_code == 400
    # Wrong-password collapses to the GENERIC validation Problem Details —
    # NO distinct `type` URI (code-review P18 — Story 1.5 review 2026-05-27).
    body = res.json()
    assert body["type"] == _GENERIC_VALIDATION_TYPE
    assert "errors" in body  # DRF flattened serializer errors
    assert "non_field_errors" in body["errors"]


def test_login_unknown_email_returns_400_generic(api_client):
    # No factory call — email doesn't exist
    res = api_client.post(
        reverse("rest_login"),
        {"email": "ghost@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code == 400
    # Same shape as wrong-password case — no enumeration leak.
    body = res.json()
    assert body["type"] == _GENERIC_VALIDATION_TYPE
    assert "errors" in body
    assert "non_field_errors" in body["errors"]


def test_login_failed_writes_audit_row_with_email_hash(api_client):
    _make_active_user("alice@example.test")
    api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": "wrong"},
        format="json",
    )
    row = AuditLog.objects.filter(action="auth.login_failed").first()
    assert row is not None
    assert row.subject_id is not None  # email matched a real user
    assert len(row.metadata.get("email_hashed", "")) == 64


def test_login_suspended_user_returns_403(api_client):
    user = _make_active_user("alice@example.test")
    user.status = UserStatus.SUSPENDED
    user.save(update_fields=["status"])

    res = api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code == 403, res.content
    body = res.json()
    assert body["type"].endswith("/account-suspended")


def test_login_email_unverified_returns_403_with_resend_hint(api_client):
    EmailUnverifiedUserFactory(email="alice@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": "alice@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code == 403, res.content
    body = res.json()
    assert body["type"].endswith("/email-not-verified")
    # `resend_endpoint` is a top-level RFC 7807 extension, NOT a field-level
    # validation error (code-review P12 — Story 1.5 review 2026-05-27).
    assert body["resend_endpoint"] == "/api/v1/auth/registration/resend-email/"
    assert "errors" not in body


def test_login_pending_parental_consent_allows_limited_mode(api_client):
    """Sub-15 user with pending parental consent CAN log in (Story 1.4 limited mode)."""
    user = _make_active_user("kid@example.test")
    user.status = UserStatus.PENDING_PARENTAL_CONSENT
    user.email_verified_at = None
    user.save(update_fields=["status", "email_verified_at"])

    res = api_client.post(
        reverse("rest_login"),
        {"email": "kid@example.test", "password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    assert res.json()["user"]["is_fully_active"] is False
