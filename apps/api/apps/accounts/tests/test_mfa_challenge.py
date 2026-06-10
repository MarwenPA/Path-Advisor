"""MFA challenge endpoint — Story 1.6 §AC3, §AC4, §AC5.

Covers TOTP + recovery code paths, lockout orthogonality, single-use blacklist.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.accounts.models import MfaProfile, UserRole
from apps.accounts.services import mfa_session as mfa_session_service
from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


def _make_enrolled_user(email="enrolled@example.test", role=UserRole.STUDENT):
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email, role=role)
    # Code-review P21 — explicit set_password defends against UserFactory default rotation.
    user.set_password(_PWD)
    user.save(update_fields=["password"])
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    static = StaticDevice.objects.create(user=user, name="default", confirmed=True)
    # Pre-load 8 recovery codes so we can test the recovery path
    StaticToken.objects.bulk_create(
        [StaticToken(device=static, token=f"abcd-{i:04d}-efgh") for i in range(8)]
    )
    MfaProfile.objects.create(user=user, enrolled_at=timezone.now())
    return user


def _valid_totp(user):
    from django_otp.oath import totp

    device = TOTPDevice.objects.get(user=user, confirmed=True)
    return str(totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits)).zfill(
        device.digits
    )


def _issue_challenge_token(user, ip="127.0.0.1"):
    return mfa_session_service.issue(user=user, stage="mfa_pending", ip=ip)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient(REMOTE_ADDR="127.0.0.1")


# ---------------------------------------------------------------------------
# TOTP path
# ---------------------------------------------------------------------------


def test_challenge_with_valid_totp_posts_session_cookie(api_client):
    user = _make_enrolled_user()
    token = _issue_challenge_token(user)

    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    assert res.status_code == 200, res.content
    assert "sessionid" in res.cookies
    assert res.cookies["sessionid"].value
    assert res.json()["user"]["email"] == user.email
    assert AuditLog.objects.filter(action="auth.mfa_challenge_passed", subject_id=user.id).exists()


def test_challenge_with_invalid_totp_returns_400_no_cookie(api_client):
    user = _make_enrolled_user()
    token = _issue_challenge_token(user)

    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": "000000", "method": "totp"},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-challenge-failed")
    assert "sessionid" not in res.cookies or res.cookies["sessionid"].value == ""
    assert AuditLog.objects.filter(action="auth.mfa_challenge_failed", subject_id=user.id).exists()


def test_challenge_consumes_mfa_session(api_client):
    user = _make_enrolled_user()
    token = _issue_challenge_token(user)
    api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    # Replay
    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    assert res.status_code == 400
    # Code-review P15 — consumed tokens now surface as a distinct error type
    # so the frontend can route to "your session was already used" UX rather
    # than the generic "invalid".
    assert res.json()["type"].endswith("/mfa-session-consumed")


def test_challenge_expired_session_returns_mfa_session_expired(api_client, settings):
    settings.MFA_SESSION_TTL_SECONDS = -1  # already expired
    user = _make_enrolled_user()
    token = _issue_challenge_token(user)

    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-session-expired")


# ---------------------------------------------------------------------------
# Recovery code path
# ---------------------------------------------------------------------------


def test_challenge_with_recovery_code_succeeds_and_consumes_code(api_client):
    user = _make_enrolled_user()
    token = _issue_challenge_token(user)

    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": "abcd-0000-efgh", "method": "recovery"},
        format="json",
    )
    assert res.status_code == 200, res.content
    assert "sessionid" in res.cookies

    # Code consumed — count drops to 7
    static = StaticDevice.objects.get(user=user)
    assert StaticToken.objects.filter(device=static).count() == 7

    # Audit row uses the `auth.mfa_recovery_code_used` action
    row = AuditLog.objects.filter(action="auth.mfa_recovery_code_used", subject_id=user.id).first()
    assert row is not None
    assert row.metadata.get("remaining_codes") == 7


def test_challenge_with_already_used_recovery_code_fails(api_client):
    user = _make_enrolled_user()
    token = _issue_challenge_token(user)
    # Use the code once
    api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": "abcd-0000-efgh", "method": "recovery"},
        format="json",
    )
    # Issue a fresh challenge token (the first was consumed)
    token2 = _issue_challenge_token(user)
    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token2, "code": "abcd-0000-efgh", "method": "recovery"},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-challenge-failed")


# ---------------------------------------------------------------------------
# Lockout orthogonality — MFA failures fill the SAME counter as password
# ---------------------------------------------------------------------------


def test_repeated_mfa_failures_trip_account_lockout(api_client, settings):
    settings.LOGIN_FAIL_THRESHOLD = 3
    user = _make_enrolled_user()

    for _ in range(3):
        token = _issue_challenge_token(user)
        api_client.post(
            reverse("mfa_challenge"),
            {"mfa_session": token, "code": "000000", "method": "totp"},
            format="json",
        )

    user.refresh_from_db()
    assert user.locked_until is not None, (
        "3 wrong TOTP codes should trip the per-account lockout (Story 1.6 §AC5)"
    )
    # Audit row from login_security service
    assert AuditLog.objects.filter(action="auth.account_locked", subject_id=user.id).exists()


def test_successful_mfa_clears_lockout_counter(api_client, settings):
    settings.LOGIN_FAIL_THRESHOLD = 5
    user = _make_enrolled_user()

    # 3 wrong attempts
    for _ in range(3):
        token = _issue_challenge_token(user)
        api_client.post(
            reverse("mfa_challenge"),
            {"mfa_session": token, "code": "000000", "method": "totp"},
            format="json",
        )

    # django-otp's ThrottlingMixin parks the device for `throttle_factor *
    # 2 ** failure_count` seconds after each failure. Reset it manually so
    # the subsequent valid-code attempt is not refused by the throttle
    # window itself (we're testing OUR lockout, not django-otp's).
    device = TOTPDevice.objects.get(user=user)
    device.throttle_reset(commit=True)

    # Correct TOTP — full login complete → counter cleared
    token = _issue_challenge_token(user)
    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    assert res.status_code == 200

    # 4 more wrong — still under threshold (counter started fresh)
    for _ in range(4):
        token = _issue_challenge_token(user)
        api_client.post(
            reverse("mfa_challenge"),
            {"mfa_session": token, "code": "000000", "method": "totp"},
            format="json",
        )
    user.refresh_from_db()
    assert user.locked_until is None


# ---------------------------------------------------------------------------
# Code-review patches — P2 too_many_attempts, P28 JTI blacklist, P12 pre-lockout
# ---------------------------------------------------------------------------


def test_threshold_trip_writes_too_many_attempts_audit_row(api_client, settings):
    """Code-review P2 — when the Nth wrong code trips the per-account lockout,
    a SECOND audit row with `reason="too_many_attempts"` is written alongside
    the per-attempt `invalid_code` rows. Spec §AC5 + §AC9 contract.
    """
    settings.LOGIN_FAIL_THRESHOLD = 3
    user = _make_enrolled_user()

    for _ in range(3):
        token = _issue_challenge_token(user)
        api_client.post(
            reverse("mfa_challenge"),
            {"mfa_session": token, "code": "000000", "method": "totp"},
            format="json",
        )

    too_many = AuditLog.objects.filter(
        action="auth.mfa_challenge_failed",
        subject_id=user.id,
        metadata__reason="too_many_attempts",
    )
    assert too_many.count() == 1, "P2 — one auth.mfa_challenge_failed with reason=too_many_attempts"


def test_repeated_failures_blacklist_jti(api_client):
    """Code-review P28 — after `MAX_FAILS_PER_TOKEN` wrong codes against the
    SAME mfa_session token, the JTI is blacklisted and further submissions
    surface `MfaSessionConsumed` even with a valid code.
    """
    from apps.accounts.services import mfa_session as mfa_session_service

    user = _make_enrolled_user()
    token = _issue_challenge_token(user)

    for _ in range(mfa_session_service.MAX_FAILS_PER_TOKEN):
        api_client.post(
            reverse("mfa_challenge"),
            {"mfa_session": token, "code": "000000", "method": "totp"},
            format="json",
        )

    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-session-consumed")


def test_locked_user_blocked_at_challenge(api_client, settings):
    """Code-review P12 — a user whose `locked_until` is set in the future is
    refused at the challenge endpoint with the generic AccountLocked Problem
    Details, even with a valid mfa_session token + valid TOTP code.
    """
    from django.utils import timezone

    user = _make_enrolled_user()
    user.locked_until = timezone.now() + timezone.timedelta(minutes=10)
    user.save(update_fields=["locked_until"])

    token = _issue_challenge_token(user)
    res = api_client.post(
        reverse("mfa_challenge"),
        {"mfa_session": token, "code": _valid_totp(user), "method": "totp"},
        format="json",
    )
    assert res.status_code == 400
    # Same generic shape as the password-lockout (Story 1.5 review D1 collapsed
    # all lockout responses to the wrong-password generic).
    assert res.json()["type"].endswith("/errors/validation") or res.json()["type"].endswith(
        "/account-locked"
    )


def test_half_login_response_scrubs_user_profile(api_client):
    """Code-review D5 — the half-login response (mfa_required=true) MUST NOT
    leak the user's email or recovery-codes count. Only the routing-essential
    fields ship before the MFA challenge completes.
    """
    from apps.accounts.models import UserRole

    user = _make_enrolled_user(role=UserRole.COUNSELOR, email="leak@example.test")

    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    body = res.json()
    assert body["mfa_required"] is True
    user_envelope = body["user"]
    assert set(user_envelope.keys()) == {
        "id",
        "role",
        "status",
        "mfa_required_by_role",
        "mfa_enrolled",
    }, f"D5 — half-login user envelope leaked extra fields: {sorted(user_envelope.keys())}"
    assert "email" not in user_envelope
    assert "mfa_recovery_codes_remaining" not in user_envelope
