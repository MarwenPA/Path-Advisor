"""Story 1.4 — signup branching tests (AC1, AC2)."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import ParentalConsent, UserStatus

pytestmark = pytest.mark.django_db


def _payload_minor(**overrides: object) -> dict[str, object]:
    payload = {
        "email": "mehdi@example.test",
        "password1": "Path-Advisor-2026!",
        "password2": "Path-Advisor-2026!",
        # 13 yo as of today — stable: relativedelta against `date.today()` ensures the
        # tests don't go red on a birthday boundary even if cron-based test runs slip.
        "birth_date": (date.today().replace(year=date.today().year - 13)).isoformat(),
        "consent_cgu_version": "2026-05-15",
        "consent_rgpd_accepted": True,
        "parent_email": "parent@example.test",
    }
    payload.update(overrides)
    return payload


def _post_signup(client: APIClient, payload: dict[str, object]):
    return client.post(reverse("rest_register"), payload, format="json")


def test_signup_under_15_with_parent_email_creates_user_and_parental_consent():
    """AC1 — happy path: < 15 + parent_email → User + ParentalConsent + 2 emails."""
    client = APIClient()
    response = _post_signup(client, _payload_minor())

    assert response.status_code == 201, response.content
    User = get_user_model()
    user = User.objects.get(email="mehdi@example.test")
    assert user.status == UserStatus.PENDING_PARENTAL_CONSENT
    assert user.email_verified_at is None
    assert user.is_fully_active is False

    consent = ParentalConsent.objects.get(student=user)
    assert consent.parent_email == "parent@example.test"
    assert consent.decision is None
    assert consent.is_expired is False
    # 60-day window — keep a generous bracket so the test is not flaky on slow CI.
    assert (consent.expires_at - consent.requested_at).days == 60

    # Two emails: child verify + parent request.
    recipients = sorted({addr for msg in mail.outbox for addr in msg.to})
    assert "mehdi@example.test" in recipients
    assert "parent@example.test" in recipients


def test_signup_under_15_without_parent_email_returns_400_parent_email_required():
    """AC2 — < 15 + no parent_email → ParentEmailRequired Problem."""
    client = APIClient()
    payload = _payload_minor()
    del payload["parent_email"]
    response = _post_signup(client, payload)

    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/parent-email-required"
    assert get_user_model().objects.filter(email="mehdi@example.test").exists() is False


def test_signup_over_15_with_parent_email_returns_400_parent_email_not_applicable():
    """AC2 — ≥ 15 + parent_email → ParentEmailNotApplicable Problem.

    Strict guard keeps the Story 1.3 happy path immutable.
    """
    client = APIClient()
    payload = _payload_minor(
        # 16 yo to clear the boundary
        birth_date=(date.today().replace(year=date.today().year - 16)).isoformat(),
    )
    response = _post_signup(client, payload)

    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/parent-email-not-applicable"


def test_signup_with_parent_email_equal_to_student_email_returns_400():
    """AC2 — parent_email == student email → ParentEmailSameAsStudent Problem."""
    client = APIClient()
    payload = _payload_minor(parent_email="mehdi@example.test")
    response = _post_signup(client, payload)

    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/parent-email-same-as-student"
