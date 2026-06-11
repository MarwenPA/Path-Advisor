"""`notify_parental_consent_revoked` Celery task tests — Story 1.10 §T7.2."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.models import ParentalConsent, ParentalConsentDecision
from apps.accounts.tasks import notify_parental_consent_revoked
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _revoked_consent():
    student = UserFactory()
    return ParentalConsent.objects.create(
        student=student,
        parent_email="parent@example.test",
        token="t-revoke-task",
        decision=ParentalConsentDecision.GRANTED,
        decided_at=timezone.now(),
        revoked_at=timezone.now(),
    )


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=True)
def test_task_sends_revoked_email_for_revoked_row(mock_send):
    consent = _revoked_consent()
    result = notify_parental_consent_revoked(str(consent.id))
    assert result is True
    mock_send.assert_called_once()
    args, _ = mock_send.call_args
    assert args[0].id == consent.id


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=True)
def test_task_skips_when_row_is_not_actually_revoked(mock_send):
    """Defensive : if `revoked_at IS NULL`, the task refuses to email — that
    would indicate a programming bug upstream we want to catch via logs.
    """
    student = UserFactory()
    consent = ParentalConsent.objects.create(
        student=student,
        parent_email="not-revoked@example.test",
        token="t-not-revoked",
        decision=ParentalConsentDecision.GRANTED,
        decided_at=timezone.now(),
    )
    result = notify_parental_consent_revoked(str(consent.id))
    assert result is False
    mock_send.assert_not_called()


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=True)
def test_task_is_a_no_op_on_missing_row(mock_send):
    result = notify_parental_consent_revoked("does-not-exist")
    assert result is False
    mock_send.assert_not_called()


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=False)
def test_task_returns_false_when_smtp_fails(mock_send):
    consent = _revoked_consent()
    result = notify_parental_consent_revoked(str(consent.id))
    assert result is False
    mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Review D5 — `revocation_notification_sent_at` idempotency gate
# ---------------------------------------------------------------------------


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=True)
def test_task_stamps_revocation_notification_sent_at_on_success(mock_send):
    """Review D5 (2) — successful SMTP must stamp the gate column."""
    consent = _revoked_consent()
    assert consent.revocation_notification_sent_at is None  # pre-condition

    notify_parental_consent_revoked(str(consent.id))

    consent.refresh_from_db()
    assert consent.revocation_notification_sent_at is not None
    mock_send.assert_called_once()


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=True)
def test_task_is_idempotent_on_re_invocation(mock_send):
    """Review D5 (1) — a second invocation against an already-notified row
    MUST NOT call SMTP again (gate on `revocation_notification_sent_at`).
    """
    consent = _revoked_consent()
    consent.revocation_notification_sent_at = timezone.now()
    consent.save(update_fields=["revocation_notification_sent_at"])

    result = notify_parental_consent_revoked(str(consent.id))

    assert result is True
    mock_send.assert_not_called()


@patch("apps.accounts.tasks.send_revoked_to_parent", return_value=False)
def test_task_does_not_stamp_on_smtp_failure(mock_send):
    """Review D5 — SMTP returning False must NOT stamp the gate (so a
    Celery retry can re-attempt without thinking the email already went out).
    """
    consent = _revoked_consent()
    notify_parental_consent_revoked(str(consent.id))

    consent.refresh_from_db()
    assert consent.revocation_notification_sent_at is None
    mock_send.assert_called_once()
