"""Revue Epic 8 — pins for the mailer fixes (lots A & B).

Each test names the finding it locks in. The philosophy is the same as the
original 8.1 suite: test Celery's REAL semantics, never a mock of the thing
under test.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from apps.mailer.models import EmailOutbox, OutboxStatus
from apps.mailer.retention import prune_email_outbox
from apps.mailer.tasks import deliver_email, sweep_stale_outbox

pytestmark = pytest.mark.django_db


def _row(**overrides) -> EmailOutbox:
    defaults = dict(
        to="eleve-review@test.local",
        template_app="notifications",
        template_base="email/parcoursup_milestone",
        context={
            "subject": "Objet calme",
            "intro": "Voici où on en est.",
            "checklist": ["Relire tes paris"],
            "cta_label": "Revoir mes paris",
            "cta_url": "https://path-advisor.fr/mes-paris",
        },
    )
    defaults.update(overrides)
    return EmailOutbox.objects.create(**defaults)


# ---------------------------------------------------------------------------
# P1-2a — CAS claim
# ---------------------------------------------------------------------------


def test_claim_increments_attempts_atomically():
    row = _row()
    assert deliver_email.apply(args=[row.pk]).get() == "sent"
    row.refresh_from_db()
    assert row.attempts == 1  # F("attempts") + 1, not read-modify-write


def test_failed_row_is_not_claimable():
    row = _row(status=OutboxStatus.FAILED)
    assert deliver_email.apply(args=[row.pk]).get() == "not-claimed:failed"
    assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# P2-11 — opt-out honoured at DELIVERY time
# ---------------------------------------------------------------------------


def test_delivery_skips_a_user_who_opted_out_after_enqueue(django_user_model):
    from apps.core.rls_testing import as_path_admin
    from apps.notifications.models import NotificationCategory, NotificationPreference

    with as_path_admin():
        user = django_user_model.objects.create_user(
            email="optout-delivery@test.local", password="Strong1!pass"
        )
        row = _row(
            to=user.email,
            notification_user_id=user.id,
            notification_category=NotificationCategory.PARCOURSUP_CALENDAR,
        )
        # The unsubscribe lands BETWEEN enqueue and delivery (retry window).
        NotificationPreference.objects.create(
            user=user, category=NotificationCategory.PARCOURSUP_CALENDAR, enabled=False
        )

    assert deliver_email.apply(args=[row.pk]).get() == "skipped-opted-out"
    assert len(mail.outbox) == 0
    row.refresh_from_db()
    assert row.status == OutboxStatus.SKIPPED  # terminal, prunable


# ---------------------------------------------------------------------------
# P2-6 — footer built at render time, token never persisted
# ---------------------------------------------------------------------------


def test_footer_is_rendered_but_never_persisted(django_user_model):
    from apps.core.rls_testing import as_path_admin
    from apps.notifications.models import NotificationCategory

    with as_path_admin():
        user = django_user_model.objects.create_user(
            email="footer-render@test.local", password="Strong1!pass"
        )
    row = _row(
        to=user.email,
        notification_user_id=user.id,
        notification_category=NotificationCategory.PARCOURSUP_CALENDAR,
    )

    assert deliver_email.apply(args=[row.pk]).get() == "sent"
    body = mail.outbox[0].body
    assert "/desinscription/" in body  # the footer DID ride along
    assert "/parametres/notifications" in body
    # ... but the capability URL lives nowhere at rest.
    row.refresh_from_db()
    assert "unsubscribe_url" not in row.context
    assert "desinscription" not in str(row.context)


# ---------------------------------------------------------------------------
# P1-1 — sweeper: no row may be lost silently
# ---------------------------------------------------------------------------


def test_sweeper_requeues_orphan_and_stale_rows_only():
    now = timezone.now()
    # Orphan: QUEUED, never attempted, older than the fresh grace.
    orphan = _row()
    EmailOutbox.objects.filter(pk=orphan.pk).update(created_at=now - timedelta(minutes=20))
    # Waiting on its retry ETA: QUEUED, attempts>0, recent transition — must
    # NOT be swept (its countdown can legitimately reach 60 min).
    waiting = _row(attempts=3)
    EmailOutbox.objects.filter(pk=waiting.pk).update(
        created_at=now - timedelta(hours=3), updated_at=now - timedelta(minutes=30)
    )
    # Lost retry: QUEUED, attempts>0, no transition past the retry horizon.
    lost = _row(attempts=3)
    EmailOutbox.objects.filter(pk=lost.pk).update(
        created_at=now - timedelta(hours=5), updated_at=now - timedelta(minutes=90)
    )
    # Crashed mid-send: stale SENDING.
    crashed = _row(status=OutboxStatus.SENDING)
    EmailOutbox.objects.filter(pk=crashed.pk).update(updated_at=now - timedelta(minutes=45))
    # Fresh row: untouched.
    fresh = _row()

    with patch.object(deliver_email, "delay") as delay:
        counts = sweep_stale_outbox.apply().get()

    requeued = {call.args[0] for call in delay.call_args_list}
    assert requeued == {orphan.pk, lost.pk, crashed.pk}
    assert counts == {"requeued_fresh": 1, "requeued_retrying": 1, "requeued_sending": 1}
    crashed.refresh_from_db()
    assert crashed.status == OutboxStatus.QUEUED  # flipped back for the CAS
    fresh.refresh_from_db()
    assert fresh.status == OutboxStatus.QUEUED
    assert fresh.pk not in requeued


# ---------------------------------------------------------------------------
# P3 — retry_failed_emails is concurrent-safe
# ---------------------------------------------------------------------------


def test_retry_failed_requeues_conditionally(capsys):
    from django.core.management import call_command

    failed = _row(status=OutboxStatus.FAILED, attempts=9, last_error="SMTPException: down")
    already_queued = _row()  # someone else's replay won the race

    with patch.object(deliver_email, "delay") as delay:
        call_command("retry_failed_emails")

    assert {call.args[0] for call in delay.call_args_list} == {failed.pk}
    failed.refresh_from_db()
    assert failed.status == OutboxStatus.QUEUED
    assert failed.attempts == 0
    assert failed.last_error == ""
    already_queued.refresh_from_db()
    assert already_queued.attempts == 0  # untouched


# ---------------------------------------------------------------------------
# P0-2 — retention core: terminal rows pruned, in-flight rows kept
# ---------------------------------------------------------------------------


def test_prune_removes_terminal_rows_and_keeps_in_flight():
    old = timezone.now() - timedelta(days=120)
    keep_queued = _row()
    keep_sending = _row(status=OutboxStatus.SENDING)
    gone_sent = _row(status=OutboxStatus.SENT)
    gone_failed = _row(status=OutboxStatus.FAILED)
    gone_skipped = _row(status=OutboxStatus.SKIPPED)
    for row in (keep_queued, keep_sending, gone_sent, gone_failed, gone_skipped):
        EmailOutbox.objects.filter(pk=row.pk).update(created_at=old)
    recent_sent = _row(status=OutboxStatus.SENT)

    deleted = prune_email_outbox(days=90)

    assert deleted == 3
    remaining = set(EmailOutbox.objects.values_list("pk", flat=True))
    assert remaining == {keep_queued.pk, keep_sending.pk, recent_sent.pk}


# ---------------------------------------------------------------------------
# P0-3 — hard delete purges the account's outbox history
# ---------------------------------------------------------------------------


def test_outbox_rows_do_not_survive_hard_delete(django_capture_on_commit_callbacks):
    """Art. 17: address, matched profession, school comments and live
    unsubscribe tokens must not outlive the account. The completion email's
    own row is the one documented exception (DPO note 8.1), bounded by the
    daily prune."""
    from apps.accounts.services import account_deletion as deletion_service
    from apps.accounts.tests.factories import UserFactory

    password = "Path-Advisor-2026!"
    user = UserFactory(email="art17@test.local", password=password)
    with django_capture_on_commit_callbacks(execute=False):
        deletion = deletion_service.request_deletion(user=user, password=password)
    EmailOutbox.objects.all().delete()  # drop the confirmation email noise

    _row(to=user.email, status=OutboxStatus.SENT)
    _row(to=user.email.upper(), status=OutboxStatus.FAILED)  # case-insensitive
    stranger_row = _row(to="autre-eleve@test.local", status=OutboxStatus.SENT)

    deletion.hard_delete_after = timezone.now() - timedelta(days=1)
    deletion.save(update_fields=["hard_delete_after"])
    with (
        django_capture_on_commit_callbacks(execute=False),
        patch.object(deletion_service, "_purge_s3_prefixes", return_value=(0, [])),
    ):
        deletion_service.hard_delete(deletion)

    remaining_to = list(EmailOutbox.objects.values_list("to", flat=True))
    assert stranger_row.to in remaining_to  # never touch other recipients
    # The ONLY row left for the erased address is the completion email.
    account_rows = EmailOutbox.objects.filter(to__iexact=user.email)
    assert account_rows.count() == 1
    assert "deletion" in account_rows.get().template_base
