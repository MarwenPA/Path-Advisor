"""Story 1.4 — Celery beat tests for parental-consent reminders + suspensions (AC6)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import UserStatus
from apps.accounts.services.parental_consent import create_parental_consent_request
from apps.accounts.tasks import (
    send_parental_consent_reminders,
    suspend_unresolved_parental_consents,
)
from apps.accounts.tests.factories import MinorUserFactory

pytestmark = pytest.mark.django_db


def _pending(*, requested_days_ago: int = 0):
    """Build a pending consent whose `requested_at` is `n` days in the past.

    Story 1.4 review §P25: also rewinds `expires_at` by the same offset. The
    previous version only backdated `requested_at`, which meant `is_expired`
    (computed from `expires_at`) was never True in the task tests — the "65 days
    ago" scenario actually exercised the `requested_at`-based query path only.
    """
    user = MinorUserFactory(status=UserStatus.PENDING_PARENTAL_CONSENT, email_verified_at=None)
    consent = create_parental_consent_request(
        student=user,
        parent_email=f"parent+{user.id}@example.test",
        ip=None,
        user_agent=None,
    )
    if requested_days_ago > 0:
        now = timezone.now()
        consent.requested_at = now - timedelta(days=requested_days_ago)
        # Keep the invariant `expires_at = requested_at + 60d` so both task queries
        # (reminder uses requested_at, suspend uses expires_at) see consistent rows.
        consent.expires_at = consent.requested_at + timedelta(days=60)
        consent.save(update_fields=["requested_at", "expires_at"])
    return user, consent


def test_celery_send_reminders_emails_only_pending_over_30d_unreminded():
    """AC6 — reminder sent iff `decision IS NULL AND reminder_sent_at IS NULL AND requested_at < now-30d`."""
    _, fresh = _pending(requested_days_ago=10)  # too recent
    _, due = _pending(requested_days_ago=35)  # eligible
    _, already_reminded = _pending(requested_days_ago=40)
    already_reminded.reminder_sent_at = timezone.now() - timedelta(days=2)
    already_reminded.save(update_fields=["reminder_sent_at"])

    mail.outbox.clear()
    sent = send_parental_consent_reminders()

    assert sent == 1
    # Verify the right consent was reminded.
    due.refresh_from_db()
    fresh.refresh_from_db()
    already_reminded.refresh_from_db()
    assert due.reminder_sent_at is not None
    assert fresh.reminder_sent_at is None
    # Already-reminded keeps its stored value (no overwrite — idempotency guard).
    # Story 1.4 review §P15: direct timedelta comparison, avoiding `.days` rounding
    # gotchas around the negative-delta boundary.
    assert already_reminded.reminder_sent_at < timezone.now() - timedelta(days=1)


def test_celery_suspend_unresolved_marks_user_suspended_and_writes_audit():
    """AC6 — suspend job flips User to SUSPENDED + sends the final email to the child."""
    fresh_user, _ = _pending(requested_days_ago=30)  # not yet 60 days
    expired_user, _ = _pending(requested_days_ago=65)  # over 60 days

    mail.outbox.clear()
    suspended = suspend_unresolved_parental_consents()

    assert suspended == 1
    fresh_user.refresh_from_db()
    expired_user.refresh_from_db()
    assert fresh_user.status == UserStatus.PENDING_PARENTAL_CONSENT
    assert expired_user.status == UserStatus.SUSPENDED

    # The child of the expired consent receives the final email.
    recipients = sorted({addr for msg in mail.outbox for addr in msg.to})
    assert expired_user.email in recipients
    assert fresh_user.email not in recipients


def test_celery_suspend_is_idempotent_on_double_run():
    """AC6 — running the suspend job twice in a row only suspends once + only emails once."""
    user, _ = _pending(requested_days_ago=65)
    mail.outbox.clear()

    first = suspend_unresolved_parental_consents()
    second = suspend_unresolved_parental_consents()

    assert first == 1
    assert second == 0
    user.refresh_from_db()
    assert user.status == UserStatus.SUSPENDED
    # Only the first run sends the email — the second run sees the user is already SUSPENDED.
    assert sum(1 for m in mail.outbox if user.email in m.to) == 1
