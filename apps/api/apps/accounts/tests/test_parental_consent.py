"""Story 1.4 — parental-consent decide endpoint tests (AC4, AC5, AC8)."""

from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.accounts.services.parental_consent import create_parental_consent_request
from apps.accounts.tests.factories import EmailUnverifiedUserFactory, MinorUserFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db

_VALID_HASH = "a" * 64


def _make_pending_consent(*, email_verified: bool = False, age_status: str = "pending"):
    user = MinorUserFactory(
        email_verified_at=timezone.now() if email_verified else None,
        status=UserStatus.PENDING_PARENTAL_CONSENT
        if age_status == "pending"
        else UserStatus.ACTIVE,
    )
    consent = create_parental_consent_request(
        student=user,
        parent_email="parent@example.test",
        ip="1.2.3.4",
        user_agent="Mozilla/5.0",
    )
    return user, consent


def _decide_url(token: str) -> str:
    return reverse("accounts:parental-consent-decide", kwargs={"token": token})


def _payload(decision: str, content_hash: str = _VALID_HASH) -> dict[str, str]:
    return {
        "decision": decision,
        "content_hash": content_hash,
        "accepted_at": "2026-05-17T12:00:00Z",
    }


def test_parental_consent_decide_granted_activates_user_when_email_verified():
    """AC5 — granted + email already verified → User = ACTIVE."""
    user, consent = _make_pending_consent(email_verified=True)
    client = APIClient()
    response = client.post(_decide_url(consent.token), _payload("granted"), format="json")

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["decision"] == "granted"
    user.refresh_from_db()
    assert user.status == UserStatus.ACTIVE
    assert user.is_fully_active is True


def test_parental_consent_decide_granted_keeps_pending_when_email_not_verified():
    """AC5 — granted + email NOT verified → User stays pending_parental_consent (no-op)."""
    user, consent = _make_pending_consent(email_verified=False)
    client = APIClient()
    response = client.post(_decide_url(consent.token), _payload("granted"), format="json")

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.status == UserStatus.PENDING_PARENTAL_CONSENT
    assert user.is_fully_active is False


def test_parental_consent_decide_refused_suspends_user_and_records_audit():
    """AC5 — refused → User = SUSPENDED + audit row with decision=refused."""
    user, consent = _make_pending_consent(email_verified=True)
    client = APIClient()
    audit_before = AuditLog.objects.filter(action="parental_consent.decided").count()

    response = client.post(_decide_url(consent.token), _payload("refused"), format="json")

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.status == UserStatus.SUSPENDED
    audit_after = AuditLog.objects.filter(action="parental_consent.decided").count()
    assert audit_after == audit_before + 1


def test_parental_consent_decide_with_invalid_token_returns_404():
    client = APIClient()
    response = client.post(_decide_url("not-a-real-token"), _payload("granted"), format="json")
    assert response.status_code == 404
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/parental-consent-not-found"


def test_parental_consent_decide_after_60_days_returns_409():
    """AC4 — token past `expires_at` → 409 even if decision is still NULL."""
    _, consent = _make_pending_consent()
    # Force-expire the consent by rewinding requested_at/expires_at.
    consent.requested_at = timezone.now() - timedelta(days=61)
    consent.expires_at = timezone.now() - timedelta(days=1)
    consent.save(update_fields=["requested_at", "expires_at"])

    client = APIClient()
    response = client.post(_decide_url(consent.token), _payload("granted"), format="json")

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://path-advisor.fr/errors/parental-consent-already-decided"


def test_parental_consent_decide_idempotency_returns_409_on_second_call():
    """AC4 — re-deciding after a grant is forbidden (single-use semantics)."""
    _, consent = _make_pending_consent(email_verified=True)
    client = APIClient()
    first = client.post(_decide_url(consent.token), _payload("granted"), format="json")
    assert first.status_code == 200

    second = client.post(_decide_url(consent.token), _payload("granted"), format="json")
    assert second.status_code == 409


def test_audit_log_for_decision_uses_hashed_parent_email_not_plaintext():
    """AC4 — `parental_consent.decided` audit row carries `parent_email_hash`, not plaintext."""
    _, consent = _make_pending_consent(email_verified=True)
    client = APIClient()
    client.post(_decide_url(consent.token), _payload("granted"), format="json")

    audit = AuditLog.objects.filter(action="parental_consent.decided").latest("created_at")
    expected_hash = hashlib.sha256(consent.parent_email.encode("utf-8")).hexdigest()
    assert audit.metadata["parent_email_hash"] == expected_hash
    assert "parent@example.test" not in str(audit.metadata)


def test_parental_consent_status_returns_masked_email_only():
    """AC4 — GET /status/ never returns the child's full email."""
    _, consent = _make_pending_consent()
    client = APIClient()
    url = reverse("accounts:parental-consent-status", kwargs={"token": consent.token})
    response = client.get(url)

    assert response.status_code == 200
    body = response.json()
    assert "***" in body["student_email_masked"]
    assert consent.student.email not in body["student_email_masked"]


def test_parental_consent_resend_requires_authenticated_student():
    """AC7 — `/resend/` is auth-protected; an anonymous call returns 401 Problem."""
    client = APIClient()
    response = client.post(reverse("accounts:parental-consent-resend"))
    assert response.status_code == 401


def test_parental_consent_resend_authenticated_student_sends_email():
    """AC7 — authenticated student with a pending consent → 200 + reminder_sent_at set."""
    user, consent = _make_pending_consent()
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(reverse("accounts:parental-consent-resend"))

    assert response.status_code == 200
    consent.refresh_from_db()
    assert consent.reminder_sent_at is not None


def test_parental_consent_resend_returns_404_when_no_pending_consent():
    """AC7 — authenticated student with no pending consent → 404 Problem."""
    user = EmailUnverifiedUserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(reverse("accounts:parental-consent-resend"))
    assert response.status_code == 404


def test_minor_email_verify_does_not_bypass_parental_consent():
    """Story 1.4 review §P1 — CRITICAL regression guard.

    A child in `pending_parental_consent` who clicks their verify-email link
    must NOT auto-promote to `ACTIVE`. Without this guard, the entire legal
    opt-in is bypassable in 2 clicks (signup → click verify-email).
    """
    from apps.accounts.services.auth_service import mark_email_verified

    user, consent = _make_pending_consent(email_verified=False)
    assert user.status == UserStatus.PENDING_PARENTAL_CONSENT

    mark_email_verified(user)
    user.refresh_from_db()

    # Email is verified but status stays pending — parent must still grant.
    assert user.email_verified_at is not None
    assert user.status == UserStatus.PENDING_PARENTAL_CONSENT
    assert user.is_fully_active is False


def test_minor_email_verify_after_parent_grant_transitions_to_active():
    """Story 1.4 review §P1 — symmetric path: when the parent has already granted
    and the child then verifies email, status should flip to ACTIVE.
    """
    from apps.accounts.services.auth_service import mark_email_verified
    from apps.accounts.services.parental_consent import record_decision

    user, consent = _make_pending_consent(email_verified=False)
    # Parent grants first — status stays pending because email not yet verified.
    record_decision(
        consent=consent,
        decision="granted",
        content_hash=_VALID_HASH,
        client_accepted_at=timezone.now(),
    )
    user.refresh_from_db()
    assert user.status == UserStatus.PENDING_PARENTAL_CONSENT

    # Then child verifies email — now both gates pass → ACTIVE.
    mark_email_verified(user)
    user.refresh_from_db()
    assert user.status == UserStatus.ACTIVE
    assert user.is_fully_active is True


def test_parental_consent_url_ordering_routes_resend_before_dynamic_token():
    """Story 1.4 review §P21 — pin URL order.

    `parental-consent/resend/` MUST resolve to the resend view, NOT to
    `parental-consent/<str:token>/` with `token="resend"`. A future reorder of
    `urlpatterns` could silently break this; this test guards against it.
    """
    url = reverse("accounts:parental-consent-resend")
    match = __import__("django").urls.resolve(url)
    assert match.url_name == "parental-consent-resend"
    # Confirm the token view does NOT capture the literal "resend".
    token_match = __import__("django").urls.resolve("/api/v1/auth/parental-consent/resend/")
    assert token_match.url_name == "parental-consent-resend"
