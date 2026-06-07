"""End-to-end MFA login flow — Story 1.6 §AC1, §AC3.

Covers the gate at `ThrottledLoginView.post`:
- Non-MFA B2C user: classic 200 + `{"user": {...}}` + session cookie.
- Staff (counselor) with no profile yet: 200 + `mfa_required=true`,
  `mfa_enrollment_required=true`, `mfa_session` token, NO session cookie.
- Enrolled user (B2C opted-in OR staff): 200 + `mfa_required=true`,
  `mfa_enrollment_required=false`, `mfa_session`, NO session cookie.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import MfaProfile, UserRole
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

_PWD = "Path-Advisor-2026!"


def _make_active_user(*, role=UserRole.STUDENT, email="alice@example.test"):
    """Helper — sets the password explicitly so the helper doesn't silently
    regress to a wrong-password result if UserFactory's default ever rotates
    (code-review P21).
    """
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email, role=role)
    user.set_password(_PWD)
    user.save(update_fields=["password"])
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    return user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# ---------------------------------------------------------------------------
# B2C non-enrolé — happy path unchanged from Story 1.5
# ---------------------------------------------------------------------------


def test_b2c_login_without_mfa_returns_user_and_session_cookie(api_client):
    user = _make_active_user(role=UserRole.STUDENT, email="alice@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert body["user"]["email"] == user.email
    assert body["user"]["mfa_required_by_role"] is False
    assert body["user"]["mfa_enrolled"] is False
    assert "mfa_required" not in body
    # Session cookie posted
    assert "sessionid" in res.cookies


# ---------------------------------------------------------------------------
# Staff (counselor) first login — forces enrollment
# ---------------------------------------------------------------------------


def test_staff_first_login_returns_mfa_enrollment_required_and_no_cookie(api_client):
    user = _make_active_user(role=UserRole.COUNSELOR, email="conseillere@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert body["mfa_required"] is True
    assert body["mfa_enrollment_required"] is True
    assert isinstance(body.get("mfa_session"), str)
    assert len(body["mfa_session"]) > 20
    # Session cookie MUST NOT be posted — login is half-done
    assert "sessionid" not in res.cookies or res.cookies["sessionid"].value == ""
    # `user.mfa_required_by_role` exposed for the frontend
    assert body["user"]["mfa_required_by_role"] is True
    assert body["user"]["mfa_enrolled"] is False


def test_school_admin_first_login_also_forces_enrollment(api_client):
    user = _make_active_user(role=UserRole.SCHOOL_ADMIN, email="ecole@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    body = res.json()
    assert body["mfa_required"] is True
    assert body["mfa_enrollment_required"] is True


def test_path_admin_first_login_also_forces_enrollment(api_client):
    user = _make_active_user(role=UserRole.PATH_ADMIN, email="admin@example.test")
    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    body = res.json()
    assert body["mfa_required"] is True
    assert body["mfa_enrollment_required"] is True


# ---------------------------------------------------------------------------
# Already-enrolled user — challenge, no enrollment
# ---------------------------------------------------------------------------


def _mark_enrolled(user, *, confirmed_totp=True):
    """Helper: create the django-otp + MfaProfile rows so `has_mfa_enrolled` is True."""
    from django_otp.plugins.otp_totp.models import TOTPDevice

    TOTPDevice.objects.create(user=user, name="default", confirmed=confirmed_totp)
    MfaProfile.objects.create(user=user, enrolled_at=timezone.now())


def test_enrolled_b2c_login_returns_mfa_challenge_required(api_client):
    user = _make_active_user(role=UserRole.STUDENT, email="enrolled@example.test")
    _mark_enrolled(user)

    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert body["mfa_required"] is True
    assert body["mfa_enrollment_required"] is False
    assert isinstance(body.get("mfa_session"), str)
    assert "sessionid" not in res.cookies or res.cookies["sessionid"].value == ""


def test_enrolled_staff_with_dpo_reset_returns_enrollment_required(api_client):
    """DPO reset flag forces the user back through enrollment at next login."""
    user = _make_active_user(role=UserRole.COUNSELOR, email="reset@example.test")
    _mark_enrolled(user)
    profile = user.mfa_profile
    profile.requires_enrollment_at_next_login = True
    profile.save()

    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    body = res.json()
    assert body["mfa_required"] is True
    assert body["mfa_enrollment_required"] is True


# ---------------------------------------------------------------------------
# Lockout-clear semantic move (Story 1.5 carry-over)
# ---------------------------------------------------------------------------


def test_password_only_success_does_NOT_clear_lockout_for_mfa_user(api_client, settings):
    """Story 1.6 semantic move — an MFA user's password-only success leaves
    the failed-attempt counter intact. Only a full MFA challenge clears it.
    """
    settings.LOGIN_FAIL_THRESHOLD = 3
    user = _make_active_user(role=UserRole.COUNSELOR, email="lock@example.test")
    _mark_enrolled(user)

    # Two wrong-password attempts — counter at 2
    for _ in range(2):
        api_client.post(
            reverse("rest_login"),
            {"email": user.email, "password": "wrong"},
            format="json",
        )

    # Correct password — but MFA pending. Counter must NOT reset.
    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.json()["mfa_required"] is True

    # One more wrong attempt → trip the lockout (3 total: 2 pre + 1 now).
    api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": "wrong"},
        format="json",
    )
    user.refresh_from_db()
    assert user.locked_until is not None, (
        "Lockout should fire on 3rd wrong attempt — MFA users must NOT have "
        "the counter reset on password-only success (Story 1.6 semantic move)."
    )


def test_b2c_non_mfa_login_success_clears_lockout(api_client, settings):
    """B2C non-MFA user: the password-only success IS the full login. Counter
    cleared as usual (Story 1.5 §AC4 behaviour preserved for this path).
    """
    settings.LOGIN_FAIL_THRESHOLD = 3
    user = _make_active_user(role=UserRole.STUDENT, email="b2c@example.test")

    # 2 wrong attempts
    for _ in range(2):
        api_client.post(
            reverse("rest_login"),
            {"email": user.email, "password": "wrong"},
            format="json",
        )

    # Correct password → cookie posted, counter cleared
    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.status_code == 200
    assert "mfa_required" not in res.json()

    # 2 more wrongs — still under threshold (counter started fresh).
    for _ in range(2):
        api_client.post(
            reverse("rest_login"),
            {"email": user.email, "password": "wrong"},
            format="json",
        )
    user.refresh_from_db()
    assert user.locked_until is None
