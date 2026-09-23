"""Story 8.1 — outbox contract tests.

The contract under test is AC3's core promise: **no email is ever lost
silently**. Every path leaves a durable, queryable trace — sent, or failed
with the error attached — and failed rows are replayable.

Templates: tests reuse the real `family/parent_invitation` set rather than
shipping test-only templates inside the app.
"""

from __future__ import annotations

from smtplib import SMTPException
from unittest import mock

import pytest
from celery.exceptions import Retry
from django.core import mail
from django.core.management import call_command
from django.template.exceptions import TemplateDoesNotExist
from django.utils import timezone

from apps.mailer.models import EmailOutbox, OutboxStatus
from apps.mailer.service import send_transactional
from apps.mailer.tasks import deliver_email

TEMPLATE = {"template_app": "family", "template_base": "parent_invitation"}
CONTEXT = {"invitation_url": "https://path-advisor.fr/x", "student_first_name": "Sarah"}


def _row(**overrides) -> EmailOutbox:
    fields = {
        "to": "parent@test.local",
        **TEMPLATE,
        "context": CONTEXT,
        **overrides,
    }
    return EmailOutbox.objects.create(**fields)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_send_transactional_delivers_and_marks_sent(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        row = send_transactional(to="parent@test.local", context=CONTEXT, **TEMPLATE)

    row.refresh_from_db()
    assert row.status == OutboxStatus.SENT
    assert row.attempts == 1
    assert row.sent_at is not None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["parent@test.local"]


@pytest.mark.django_db(transaction=True)
def test_rolled_back_transaction_sends_nothing(django_capture_on_commit_callbacks):
    """on_commit gating: an aborted business transaction must not email anyone."""
    from django.db import transaction

    with django_capture_on_commit_callbacks(execute=True):
        try:
            with transaction.atomic():
                send_transactional(to="parent@test.local", context=CONTEXT, **TEMPLATE)
                raise RuntimeError("business rollback")
        except RuntimeError:
            pass

    assert len(mail.outbox) == 0
    # The row itself rolled back with the transaction — no orphan.
    assert EmailOutbox.objects.count() == 0


@pytest.mark.django_db
def test_non_json_context_fails_at_call_site():
    with pytest.raises(TypeError, match="JSON-serializable"):
        send_transactional(to="x@test.local", context={"bad": object()}, **TEMPLATE)
    assert EmailOutbox.objects.count() == 0


# ---------------------------------------------------------------------------
# Task retry semantics
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_transient_smtp_failure_is_retried_not_lost():
    row = _row()
    with (
        mock.patch("apps.mailer.tasks._render_and_send", side_effect=SMTPException("boom")),
        pytest.raises(Retry),
    ):
        deliver_email.apply(args=[row.pk], throw=True).get()

    row.refresh_from_db()
    assert row.status == OutboxStatus.QUEUED  # not terminal — will retry
    assert row.attempts == 1
    assert "SMTPException: boom" in row.last_error


@pytest.mark.django_db
def test_exhausted_retries_mark_failed_loudly():
    # Real exhaustion semantics, NOT a patched `retry`: the first version of
    # this test patched `deliver_email.retry` to raise
    # MaxRetriesExceededError and thereby masked a dead branch in the task
    # (with `retry(exc=...)`, Celery re-raises the ORIGINAL exception at
    # exhaustion — the FAILED transition never fired and exhausted rows
    # stayed QUEUED forever). Pinning `max_retries=0` exercises the genuine
    # pre-retry exhaustion check instead of my assumption about Celery.
    row = _row()
    with (
        mock.patch("apps.mailer.tasks._render_and_send", side_effect=SMTPException("down")),
        mock.patch.object(deliver_email, "max_retries", 0),
    ):
        result = deliver_email.apply(args=[row.pk]).get()

    assert result == "failed"
    row.refresh_from_db()
    assert row.status == OutboxStatus.FAILED
    assert "down" in row.last_error  # the error is ON the row — never silent


@pytest.mark.django_db
def test_programming_error_fails_fast_without_retry():
    row = _row(template_base="does_not_exist")
    result = deliver_email.apply(args=[row.pk]).get()

    assert result == "failed"
    row.refresh_from_db()
    assert row.status == OutboxStatus.FAILED
    assert TemplateDoesNotExist.__name__ in row.last_error
    assert row.attempts == 1  # exactly one — retrying a bug only delays the alert


@pytest.mark.django_db
def test_redelivery_of_sent_row_is_a_noop():
    """acks_late can redeliver after a worker crash — never double-send."""
    row = _row(status=OutboxStatus.SENT, sent_at=timezone.now())
    result = deliver_email.apply(args=[row.pk]).get()
    assert result == "already-sent"
    assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_retry_failed_emails_requeues_and_delivers():
    row = _row(status=OutboxStatus.FAILED, attempts=8, last_error="old outage")
    call_command("retry_failed_emails")

    row.refresh_from_db()
    # CELERY_TASK_ALWAYS_EAGER: the requeue delivered synchronously.
    assert row.status == OutboxStatus.SENT
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_prune_keeps_queued_rows():
    old = timezone.now() - timezone.timedelta(days=120)
    sent = _row(status=OutboxStatus.SENT)
    queued = _row(status=OutboxStatus.QUEUED)
    EmailOutbox.objects.update(created_at=old)

    call_command("prune_email_outbox", "--days", "90")

    assert not EmailOutbox.objects.filter(pk=sent.pk).exists()
    # A queued row is an undelivered email — retention must never eat it.
    assert EmailOutbox.objects.filter(pk=queued.pk).exists()
