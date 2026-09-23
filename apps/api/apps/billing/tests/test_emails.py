"""Story 8.1 — AC3 outbox contract for the billing email module.

`send_premium_activated` now queues through `apps.mailer.send_transactional`;
this test proves the end-to-end "no silent loss" contract: an SMTP outage
leaves a durable, queryable `EmailOutbox` trace (queued, with attempts +
last_error) instead of the pre-8.1 swallowed `log.warning`.
"""

from __future__ import annotations

from smtplib import SMTPException
from unittest import mock

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.billing.services.emails import send_premium_activated
from apps.mailer.models import EmailOutbox, OutboxStatus
from apps.mailer.tasks import MAX_RETRIES

pytestmark = pytest.mark.django_db


def test_smtp_outage_leaves_nonsilent_outbox_row(django_capture_on_commit_callbacks):
    user = User.objects.create_user(
        email="premium@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )

    with (
        mock.patch("apps.mailer.tasks._render_and_send", side_effect=SMTPException("smtp down")),
        django_capture_on_commit_callbacks(execute=True),
    ):
        assert send_premium_activated(user) is True

    row = EmailOutbox.objects.get()
    assert row.to == "premium@test.local"
    assert row.template_app == "billing"
    assert row.template_base == "premium_activated"
    # Durable and replayable — never lost. Eager Celery runs the retry chain
    # inline, so every attempt is already accounted for on the row.
    # Story 8.1 core fix: exhausted-retryable rows now terminate FAILED
    # (the QUEUED terminal these tests first pinned was the dead-branch
    # bug this very suite surfaced — retry(exc=...) re-raises the original
    # exception, so the old MaxRetriesExceededError handler never ran).
    assert row.status == OutboxStatus.FAILED
    assert row.attempts == MAX_RETRIES + 1
    assert "SMTPException: smtp down" in row.last_error
    assert len(mail.outbox) == 0  # nothing delivered — and nothing swallowed
