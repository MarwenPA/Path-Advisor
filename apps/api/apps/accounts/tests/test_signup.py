"""Integration tests for the signup flow — Story 1.3."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, UserStatus

SIGNUP_URL = "/api/v1/auth/registration/"


def _valid_payload(**overrides):
    payload = {
        "email": "sarah@example.test",
        "password1": "Path-Advisor-2026!",
        "password2": "Path-Advisor-2026!",
        "birth_date": (date.today() - timedelta(days=365 * 18)).isoformat(),
        "consent_rgpd_accepted": True,
        "consent_cgu_version": "2026-05-15",
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def _clear_mailbox_and_cache():
    """Reset the in-memory rate-limit cache + email outbox between tests."""
    from django.core.cache import cache

    cache.clear()
    mail.outbox.clear()
    yield
    cache.clear()
    mail.outbox.clear()


@pytest.mark.django_db
def test_signup_happy_path_creates_user_in_email_unverified():
    client = APIClient()

    response = client.post(SIGNUP_URL, _valid_payload(), format="json")

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    user = User.objects.get(email="sarah@example.test")
    assert user.role == "student"
    assert user.status == UserStatus.EMAIL_UNVERIFIED
    assert user.birth_date is not None
    assert user.consent_rgpd_at is not None
    assert user.consent_cgu_version == "2026-05-15"
    assert user.email_verified_at is None
    # Email-verification message landed in the locmem outbox.
    assert len(mail.outbox) == 1
    assert "vérifie" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_signup_without_consent_rgpd_returns_400_problem():
    client = APIClient()

    response = client.post(SIGNUP_URL, _valid_payload(consent_rgpd_accepted=False), format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Either our custom DomainError (consent-rgpd-required) or DRF validation envelope.
    body = response.json()
    assert "consent" in str(body).lower() or "rgpd" in str(body).lower()
    assert not User.objects.filter(email="sarah@example.test").exists()


@pytest.mark.django_db
def test_signup_age_under_15_returns_400_problem_with_age_under_15_type():
    client = APIClient()
    underage = (date.today() - timedelta(days=365 * 10)).isoformat()

    response = client.post(SIGNUP_URL, _valid_payload(birth_date=underage), format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    # Look for our custom type anywhere in the response (DRF wraps domain errors in `errors`).
    flat = str(body).lower()
    assert "age-under-15" in flat or "moins de 15" in flat
    assert not User.objects.filter(email="sarah@example.test").exists()


@pytest.mark.django_db
def test_signup_duplicate_email_returns_400_problem_generic_message():
    client = APIClient()
    client.post(SIGNUP_URL, _valid_payload(), format="json")

    response = client.post(SIGNUP_URL, _valid_payload(), format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    detail = str(body).lower()
    # Generic message — must NOT reveal that the email already exists AND must say "impossible".
    # Previously `or` made this assertion vacuously true (cf. code review §11). Both clauses
    # are now required, so a regression that leaks "email déjà utilisée" actually fails the test.
    assert "déjà" not in detail
    assert "impossible" in detail
    # Single account in DB despite two attempts.
    assert User.objects.filter(email="sarah@example.test").count() == 1
    # Defence in depth: the Problem MUST NOT carry a field-level `errors.email` entry, which
    # would let an attacker enumerate existing addresses (CWE-203).
    assert "errors" not in body or "email" not in body.get("errors", {})


@pytest.mark.django_db
def test_signup_weak_password_returns_400_problem():
    client = APIClient()
    response = client.post(
        SIGNUP_URL, _valid_payload(password1="12345678", password2="12345678"), format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    flat = str(body).lower()
    # Django validators reject short + common + numeric passwords; at least one signal expected.
    assert any(
        token in flat for token in ("password", "mot de passe", "trop court", "courant", "numeric")
    )
    assert not User.objects.filter(email="sarah@example.test").exists()


@pytest.mark.django_db
def test_verify_email_with_valid_token_activates_account():
    """Confirm the allauth → signal → service wiring activates the user.

    The verification key is parsed from the actual outbox email body so that any
    regression in the template (broken `{{ activate_url }}`, wrong host, missing
    DPO mention) surfaces as a test failure rather than going undetected.
    """
    import re
    from urllib.parse import unquote

    from allauth.account.models import EmailAddress

    client = APIClient()
    client.post(SIGNUP_URL, _valid_payload(), format="json")

    email_address = EmailAddress.objects.get(email="sarah@example.test")
    assert not email_address.verified
    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body
    # Template MUST reference the DPO contact (cf. AC3 — code review patch).
    assert "dpo@path-advisor.fr" in email_body
    match = re.search(r"/auth/verify-email\?key=([^\s]+)", email_body)
    assert match is not None, "verification link not found in email body"
    # The adapter URL-encodes the key for transport (cf. code review §11). The verify-email
    # endpoint expects the decoded value in the JSON body.
    key = unquote(match.group(1))

    response = client.post("/api/v1/auth/registration/verify-email/", {"key": key}, format="json")

    assert response.status_code == status.HTTP_200_OK, response.json()
    user = User.objects.get(email="sarah@example.test")
    assert user.status == UserStatus.ACTIVE
    assert user.email_verified_at is not None


@pytest.mark.django_db
@pytest.mark.slow
def test_signup_rate_limited_after_5_attempts(settings):
    """6th attempt within the hour returns 429.

    `django-ratelimit` keys on the IP — APIClient defaults to 127.0.0.1.
    """
    client = APIClient()
    for i in range(5):
        payload = _valid_payload(email=f"sarah{i}@example.test")
        response = client.post(SIGNUP_URL, payload, format="json")
        # Some may fail validation (e.g. weak password) but the rate-limit counts every attempt.
        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        )

    payload = _valid_payload(email="sarah-blocked@example.test")
    response = client.post(SIGNUP_URL, payload, format="json")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    # `Retry-After` is an HTTP header — must read from headers/META, not the response body.
    retry_after = response.headers.get("Retry-After")
    assert retry_after is not None
    assert int(retry_after) >= 1
