"""MFA disable + DPO reset + regenerate recovery — Story 1.6 §AC6, §AC7.

Covers:
- B2C user can disable; staff get 403 (NFR-S2).
- Recovery-codes regenerate invalidates the prior set + returns 8 fresh codes.
- DPO `mfa.reset_by_dpo` wipes devices and forces re-enrollment at next login.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.accounts.models import MfaProfile, UserRole
from apps.accounts.services import mfa as mfa_service
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
    sd = StaticDevice.objects.create(user=user, name="default", confirmed=True)
    StaticToken.objects.bulk_create(
        [StaticToken(device=sd, token=f"abcd-{i:04d}-efgh") for i in range(8)]
    )
    MfaProfile.objects.create(user=user, enrolled_at=timezone.now())
    return user


def _valid_totp(user):
    from django_otp.oath import totp

    device = TOTPDevice.objects.get(user=user, confirmed=True)
    return str(totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits)).zfill(
        device.digits
    )


@pytest.fixture
def authed_client():
    """API client with a logged-in B2C enrolled user."""

    def _make(role=UserRole.STUDENT, email="b2c@example.test"):
        user = _make_enrolled_user(email=email, role=role)
        client = APIClient()
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        return client, user

    return _make


# ---------------------------------------------------------------------------
# disable (B2C OK, staff refused)
# ---------------------------------------------------------------------------


def test_b2c_user_can_disable_mfa(authed_client):
    client, user = authed_client(role=UserRole.STUDENT)
    res = client.post(
        reverse("mfa_disable"),
        {"password": _PWD, "code": _valid_totp(user)},
        format="json",
    )
    assert res.status_code == 200, res.content

    # Devices wiped + profile.enrolled_at cleared
    assert not TOTPDevice.objects.filter(user=user).exists()
    assert not StaticDevice.objects.filter(user=user).exists()
    user.refresh_from_db()
    assert user.has_mfa_enrolled is False

    # Audit row
    assert AuditLog.objects.filter(action="auth.mfa_disabled", subject_id=user.id).exists()


def test_staff_cannot_disable_mfa_returns_403(authed_client):
    client, user = authed_client(role=UserRole.COUNSELOR, email="conseillere@example.test")
    res = client.post(
        reverse("mfa_disable"),
        {"password": _PWD, "code": _valid_totp(user)},
        format="json",
    )
    assert res.status_code == 403
    body = res.json()
    assert body["type"].endswith("/mfa-disable-forbidden")
    # Devices remain intact
    assert TOTPDevice.objects.filter(user=user).exists()


def test_disable_with_wrong_password_returns_400(authed_client):
    client, user = authed_client(role=UserRole.STUDENT)
    res = client.post(
        reverse("mfa_disable"),
        {"password": "wrong-pwd", "code": _valid_totp(user)},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["type"].endswith("/mfa-challenge-failed")


def test_disable_with_wrong_totp_returns_400(authed_client):
    client, _user = authed_client(role=UserRole.STUDENT)
    res = client.post(
        reverse("mfa_disable"),
        {"password": _PWD, "code": "000000"},
        format="json",
    )
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# regenerate recovery codes
# ---------------------------------------------------------------------------


def test_regenerate_recovery_codes_returns_8_fresh_codes_and_invalidates_prior(
    authed_client, settings
):
    settings.MFA_RECOVERY_CODES_COUNT = 8
    client, user = authed_client()
    sd_before = StaticDevice.objects.get(user=user)
    prior_codes = list(StaticToken.objects.filter(device=sd_before).values_list("token", flat=True))

    res = client.post(
        reverse("mfa_regenerate_recovery_codes"),
        {"password": _PWD, "code": _valid_totp(user)},
        format="json",
    )
    assert res.status_code == 200, res.content
    fresh = res.json()["recovery_codes"]
    assert len(fresh) == 8

    # Prior codes are gone
    sd_after = StaticDevice.objects.get(user=user)
    current = set(StaticToken.objects.filter(device=sd_after).values_list("token", flat=True))
    assert current.isdisjoint(set(prior_codes))
    assert current == set(fresh)

    # Audit row
    assert AuditLog.objects.filter(
        action="auth.mfa_recovery_codes_regenerated", subject_id=user.id
    ).exists()


# ---------------------------------------------------------------------------
# DPO reset (service-only, no endpoint)
# ---------------------------------------------------------------------------


def test_reset_by_dpo_wipes_devices_and_forces_enrollment_at_next_login():
    from allauth.account.models import EmailAddress

    target = _make_enrolled_user(email="target-staff@example.test", role=UserRole.COUNSELOR)
    dpo = UserFactory(email="dpo@example.test", role=UserRole.PATH_ADMIN)
    EmailAddress.objects.create(user=dpo, email=dpo.email, primary=True, verified=True)

    mfa_service.reset_by_dpo(
        target_user=target,
        dpo_actor=dpo,
        reason="Lost authenticator + all recovery codes",
    )

    # Devices wiped
    assert not TOTPDevice.objects.filter(user=target).exists()
    assert not StaticDevice.objects.filter(user=target).exists()

    # Profile flagged
    profile = MfaProfile.objects.get(user=target)
    assert profile.enrolled_at is None
    assert profile.requires_enrollment_at_next_login is True

    # Audit row with the DPO as actor + reason
    row = AuditLog.objects.filter(action="auth.mfa_reset_by_dpo", subject_id=target.id).first()
    assert row is not None
    assert row.actor_id == dpo.id
    assert row.metadata.get("reason") == "Lost authenticator + all recovery codes"


def test_reset_by_dpo_followed_by_login_forces_enrollment_branch():
    """Round-trip: reset → next login → response carries
    `mfa_enrollment_required=True` even though the user has no prior unconfirmed
    TOTP device (the flag is the source of truth, not the device state).
    """
    from allauth.account.models import EmailAddress

    target = _make_enrolled_user(email="round-trip@example.test", role=UserRole.COUNSELOR)
    dpo = UserFactory(email="dpo2@example.test", role=UserRole.PATH_ADMIN)
    EmailAddress.objects.create(user=dpo, email=dpo.email, primary=True, verified=True)

    mfa_service.reset_by_dpo(target_user=target, dpo_actor=dpo, reason="Lost device")

    client = APIClient()
    res = client.post(
        reverse("rest_login"),
        {"email": target.email, "password": _PWD},
        format="json",
    )
    body = res.json()
    assert body["mfa_required"] is True
    assert body["mfa_enrollment_required"] is True
