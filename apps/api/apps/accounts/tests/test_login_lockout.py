"""Per-account login lockout — Story 1.5 §AC4.

5 failed attempts within 15 min → `User.locked_until = now + 10 min`. The
locked state surfaces as a generic 400 (same shape as wrong password) so an
attacker can't tell the lockout was triggered. Successful login clears the
counter + the lockout column.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


def _make_active_user(email: str = "alice@example.test"):
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email)
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    return user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def _tight_lockout_threshold(settings):
    """Use a 3-attempt threshold so the test runs fast; behavior is unchanged
    from the production 5-attempt cap — both go through the same code path.
    """
    settings.LOGIN_FAIL_THRESHOLD = 3
    settings.LOGIN_FAIL_WINDOW_SECONDS = 900
    settings.LOGIN_LOCK_DURATION_SECONDS = 600


def test_three_failures_trip_lockout(api_client):
    user = _make_active_user()
    url = reverse("rest_login")
    payload = {"email": user.email, "password": "wrong"}

    # 3 wrong-password attempts → trip the lockout on the 3rd.
    for _ in range(3):
        api_client.post(url, payload, format="json")

    user.refresh_from_db()
    assert user.locked_until is not None
    assert user.locked_until > timezone.now()
    # Audit row written on the trip.
    assert AuditLog.objects.filter(action="auth.account_locked", subject_id=user.id).exists()


def test_locked_user_correct_password_still_400(api_client):
    """Lockout supersedes a correct password — same generic 400, INDISTINGUISHABLE
    from wrong-password in the Problem Details body (code-review D1 collapse).
    """
    user = _make_active_user()
    user.locked_until = timezone.now() + timedelta(minutes=10)
    user.save(update_fields=["locked_until"])

    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.status_code == 400
    body = res.json()
    # Body shape collapses to the generic wrong-password validation envelope —
    # NO `/account-locked` URI, NO distinct title. Scripted attackers cannot
    # distinguish "locked" from "wrong password" via the response.
    assert body["type"] == "https://path-advisor.fr/errors/validation"
    assert body["title"] == "Validation"
    assert not body["type"].endswith("/account-locked")
    # The audit log captures the blocked-locked event (internal DPO signal).
    assert AuditLog.objects.filter(action="auth.login_blocked_locked", subject_id=user.id).exists()


def test_lockout_expires_after_cooldown(api_client):
    """Once `locked_until < now()`, login proceeds + clears the lockout column."""
    user = _make_active_user()
    user.locked_until = timezone.now() - timedelta(minutes=1)  # already expired
    user.save(update_fields=["locked_until"])

    res = api_client.post(
        reverse("rest_login"),
        {"email": user.email, "password": _PWD},
        format="json",
    )
    assert res.status_code == 200, res.content
    user.refresh_from_db()
    assert user.locked_until is None  # cleared on success


def test_successful_login_clears_failed_attempts_counter(api_client, settings):
    user = _make_active_user()
    url = reverse("rest_login")

    # 2 wrong attempts (one less than threshold) — no lockout yet.
    for _ in range(2):
        api_client.post(url, {"email": user.email, "password": "wrong"}, format="json")
    user.refresh_from_db()
    assert user.locked_until is None

    # Correct login resets the counter — verify by doing 2 more wrong
    # attempts after the success: still no lockout (counter started fresh).
    api_client.post(url, {"email": user.email, "password": _PWD}, format="json")
    for _ in range(2):
        api_client.post(url, {"email": user.email, "password": "wrong"}, format="json")
    user.refresh_from_db()
    assert user.locked_until is None


def test_unknown_email_does_not_trip_any_lockout(api_client):
    """Unknown emails have no user to lock — they only count toward IP throttle."""
    api_client.post(
        reverse("rest_login"),
        {"email": "ghost@example.test", "password": "wrong"},
        format="json",
    )
    # No User row → no lockout state to assert. Just confirm no audit
    # `auth.account_locked` row appeared (would indicate a serializer bug).
    assert not AuditLog.objects.filter(action="auth.account_locked").exists()
    assert not User.objects.filter(email="ghost@example.test").exists()
