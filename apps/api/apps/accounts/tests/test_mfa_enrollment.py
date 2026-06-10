"""MFA enrollment endpoints — Story 1.6 §AC1, §AC2.

Covers:
- POST /api/v1/auth/mfa/enroll/start/ — requires valid mfa_session, returns
  otpauth_url + qr_svg, idempotent (re-start replaces unconfirmed device).
- POST /api/v1/auth/mfa/enroll/confirm/ — requires 6-digit code, success
  posts session cookie + returns 8 recovery codes, audit row.
- mfa_session stage validation, IP-binding, single-use blacklist.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.accounts.models import MfaProfile, UserRole
from apps.accounts.services import mfa_session as mfa_session_service
from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


def _make_staff_user(email="conseillere@example.test"):
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email, role=UserRole.COUNSELOR)
    # Explicit set_password — code-review P21 (defensive vs UserFactory rotation).
    user.set_password(_PWD)
    user.save(update_fields=["password"])
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    return user


def _issue_enrollment_session(user, ip="127.0.0.1"):
    return mfa_session_service.issue(user=user, stage="mfa_enrollment_pending", ip=ip)


@pytest.fixture
def api_client() -> APIClient:
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    return client


# ---------------------------------------------------------------------------
# enroll/start
# ---------------------------------------------------------------------------


def test_start_enrollment_returns_otpauth_url_and_qr_svg(api_client):
    user = _make_staff_user()
    token = _issue_enrollment_session(user)

    res = api_client.post(
        reverse("mfa_enroll_start"),
        {"mfa_session": token},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert body["otpauth_url"].startswith("otpauth://totp/")
    assert "Path-Advisor" in body["otpauth_url"]
    assert body["account_label"] == user.email
    assert body["issuer"] == "Path-Advisor"
    # The QR is an inline SVG string — render-ready for the frontend.
    assert body["qr_svg"].lstrip().startswith("<?xml") or body["qr_svg"].lstrip().startswith("<svg")

    # An unconfirmed TOTPDevice now exists for the user
    assert TOTPDevice.objects.filter(user=user, confirmed=False).count() == 1
    # Audit row written
    assert AuditLog.objects.filter(
        action="auth.mfa_enrollment_started", subject_id=user.id
    ).exists()


def test_start_enrollment_idempotent_replaces_prior_unconfirmed_device(api_client):
    user = _make_staff_user()
    token = _issue_enrollment_session(user)

    api_client.post(reverse("mfa_enroll_start"), {"mfa_session": token}, format="json")
    first_device = TOTPDevice.objects.get(user=user, confirmed=False)

    # Re-call → mfa_session was consumed? NO — the start endpoint does NOT
    # consume the session (the user might iterate the QR code multiple times).
    # We need a fresh token to call again since `verify` does NOT consume.
    res = api_client.post(reverse("mfa_enroll_start"), {"mfa_session": token}, format="json")
    assert res.status_code == 200
    devices = TOTPDevice.objects.filter(user=user, confirmed=False)
    assert devices.count() == 1  # idempotent — old device replaced
    assert devices.first().id != first_device.id


def test_start_enrollment_refuses_invalid_mfa_session(api_client):
    res = api_client.post(
        reverse("mfa_enroll_start"),
        {"mfa_session": "obviously-not-a-real-token"},
        format="json",
    )
    assert res.status_code == 400
    body = res.json()
    assert body["type"].endswith("/mfa-session-invalid") or body["type"].endswith(
        "/mfa-session-expired"
    )


def test_start_enrollment_refuses_wrong_stage_session(api_client):
    user = _make_staff_user()
    # Issue a CHALLENGE-stage token instead of an enrollment-stage one
    wrong_token = mfa_session_service.issue(user=user, stage="mfa_pending", ip="127.0.0.1")
    res = api_client.post(
        reverse("mfa_enroll_start"),
        {"mfa_session": wrong_token},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-session-invalid")


def test_start_enrollment_refuses_ip_mismatch(api_client):
    user = _make_staff_user()
    # Token issued bound to a different IP than the request will use
    token = mfa_session_service.issue(user=user, stage="mfa_enrollment_pending", ip="9.9.9.9")
    # API client posts from 127.0.0.1 (fixture default)
    res = api_client.post(
        reverse("mfa_enroll_start"),
        {"mfa_session": token},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-session-invalid")


# ---------------------------------------------------------------------------
# enroll/confirm
# ---------------------------------------------------------------------------


def _get_valid_totp_for_user(user):
    """Pull the user's unconfirmed TOTPDevice + generate a valid current code.

    Zero-pad to `device.digits` because `totp()` returns an int — `str(1234)`
    gives `"1234"` which fails the serializer's `min_length=6`.
    """
    from django_otp.oath import totp

    device = TOTPDevice.objects.get(user=user, confirmed=False)
    code_int = totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits)
    return str(code_int).zfill(device.digits)


def test_confirm_enrollment_with_valid_code_returns_recovery_codes_and_cookie(api_client, settings):
    settings.MFA_RECOVERY_CODES_COUNT = 8
    user = _make_staff_user()
    token = _issue_enrollment_session(user)
    api_client.post(reverse("mfa_enroll_start"), {"mfa_session": token}, format="json")

    valid_code = _get_valid_totp_for_user(user)
    res = api_client.post(
        reverse("mfa_enroll_confirm"),
        {"mfa_session": token, "code": valid_code},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert len(body["recovery_codes"]) == 8
    # Format check: each `xxxx-xxxx-xxxx` is 14 chars
    assert all(len(c) == 14 and c.count("-") == 2 for c in body["recovery_codes"])
    assert body["user"]["mfa_enrolled"] is True

    # Session cookie POSTED — full login complete
    assert "sessionid" in res.cookies
    assert res.cookies["sessionid"].value

    # TOTPDevice is now confirmed
    assert TOTPDevice.objects.get(user=user).confirmed is True
    # StaticDevice + 8 StaticTokens exist
    sd = StaticDevice.objects.get(user=user)
    assert StaticToken.objects.filter(device=sd).count() == 8

    # MfaProfile.enrolled_at set
    profile = MfaProfile.objects.get(user=user)
    assert profile.enrolled_at is not None

    # Audit row
    assert AuditLog.objects.filter(action="auth.mfa_enrolled", subject_id=user.id).exists()


def test_confirm_enrollment_with_wrong_code_returns_400_and_no_recovery(api_client):
    user = _make_staff_user()
    token = _issue_enrollment_session(user)
    api_client.post(reverse("mfa_enroll_start"), {"mfa_session": token}, format="json")

    res = api_client.post(
        reverse("mfa_enroll_confirm"),
        {"mfa_session": token, "code": "000000"},
        format="json",
    )
    assert res.status_code == 400
    body = res.json()
    assert body["type"].endswith("/mfa-challenge-failed")
    # TOTPDevice stays unconfirmed
    assert TOTPDevice.objects.get(user=user).confirmed is False
    # No StaticDevice created
    assert not StaticDevice.objects.filter(user=user).exists()
    # Failed-challenge audit row exists
    assert AuditLog.objects.filter(action="auth.mfa_challenge_failed", subject_id=user.id).exists()


def test_confirm_enrollment_consumes_mfa_session(api_client):
    user = _make_staff_user()
    token = _issue_enrollment_session(user)
    api_client.post(reverse("mfa_enroll_start"), {"mfa_session": token}, format="json")
    valid_code = _get_valid_totp_for_user(user)

    res1 = api_client.post(
        reverse("mfa_enroll_confirm"),
        {"mfa_session": token, "code": valid_code},
        format="json",
    )
    assert res1.status_code == 200

    # Replaying the same token must be rejected (blacklisted)
    res2 = api_client.post(
        reverse("mfa_enroll_confirm"),
        {"mfa_session": token, "code": valid_code},
        format="json",
    )
    assert res2.status_code == 400
    # Code-review P15 — consumed tokens are distinguished from generic
    # invalid ones (UX-routable Problem Details type).
    assert res2.json()["type"].endswith("/mfa-session-consumed")


# ---------------------------------------------------------------------------
# Code-review patches — start-from-session (D3) + already-enrolled guard (P5)
# ---------------------------------------------------------------------------


def test_start_enrollment_refuses_already_enrolled_user(api_client):
    """Code-review P5 — `enroll/start/` refuses for an already-enrolled user
    so a stale `mfa_enrollment_pending` token can't create a 2nd device.
    """
    from django.utils import timezone

    from apps.accounts.models import MfaProfile

    user = _make_staff_user()
    # Mark enrolled
    TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    MfaProfile.objects.create(user=user, enrolled_at=timezone.now())

    token = _issue_enrollment_session(user)
    res = api_client.post(
        reverse("mfa_enroll_start"),
        {"mfa_session": token},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-enrollment-already-complete")


def test_start_enrollment_allows_dpo_reset_re_enrollment(api_client):
    """Code-review P5 — the `requires_enrollment_at_next_login` flag set by
    `reset_by_dpo` REOPENS the enrollment flow for an enrolled user.
    """
    from django.utils import timezone

    from apps.accounts.models import MfaProfile

    user = _make_staff_user()
    TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    MfaProfile.objects.create(
        user=user,
        enrolled_at=timezone.now(),
        requires_enrollment_at_next_login=True,
    )

    token = _issue_enrollment_session(user)
    res = api_client.post(
        reverse("mfa_enroll_start"),
        {"mfa_session": token},
        format="json",
    )
    assert res.status_code == 200


def test_start_from_session_endpoint_issues_token_for_b2c_user(authed_client_factory):
    """Code-review D3 — the B2C "Activer la MFA" CTA hits this endpoint
    instead of forcing a logout/re-login.
    """
    client, _user = authed_client_factory()
    res = client.post(reverse("mfa_enroll_start_from_session"), {}, format="json")
    assert res.status_code == 200, res.content
    body = res.json()
    assert isinstance(body["mfa_session"], str)
    assert body["mfa_enrollment_required"] is True


def test_start_from_session_refuses_already_enrolled(authed_client_factory):
    """The settings page should never render the CTA for an enrolled user,
    but the backend defends in depth (D3 + P5).
    """
    from django.utils import timezone

    from apps.accounts.models import MfaProfile

    client, user = authed_client_factory()
    TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    MfaProfile.objects.create(user=user, enrolled_at=timezone.now())

    res = client.post(reverse("mfa_enroll_start_from_session"), {}, format="json")
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-enrollment-already-complete")


@pytest.fixture
def authed_client_factory():
    """API client logged in as a B2C non-enrolled student."""
    from allauth.account.models import EmailAddress

    from apps.accounts.models import UserRole as _UserRole

    def _make(email="b2c-mfa@example.test"):
        user = UserFactory(email=email, role=_UserRole.STUDENT)
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        client = APIClient()
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        return client, user

    return _make
