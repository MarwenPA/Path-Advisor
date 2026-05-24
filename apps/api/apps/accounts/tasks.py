"""Celery tasks for the parental-consent lifecycle (Story 1.4 T5).

Both jobs are **pull-based queries** on `requested_at + N days`. This means:

- If `celery beat` is down for 3 days, no reminders/suspensions happen during those
  days, but all backlogged work catches up on the next successful run (the queries
  are stateless against `requested_at`).
- `reminder_sent_at IS NULL` is the idempotency guard for the reminder job; the
  Celery beat job can fire any number of times in a 24h window and each row is
  still reminded at most once.
- The suspension job is naturally idempotent: it only flips users that are not
  already `SUSPENDED`.

Discovery: registered via `app.autodiscover_tasks()` in `path_advisor/celery.py`,
hence the `accounts.<task_name>` task names.
"""

from __future__ import annotations

from datetime import timedelta

import structlog
from celery import shared_task
from django.utils import timezone

from apps.accounts.models import ParentalConsent, ParentalConsentDecision, UserStatus
from apps.accounts.services.parental_consent import suspend_for_unresolved_consent
from apps.accounts.services.parental_consent_email import (
    send_expired_to_child,
    send_granted_to_child,
    send_reminder_to_parent,
)

log = structlog.get_logger(__name__)

# Reminder threshold from Story 1.4 §AC6. Centralised as a constant so tests can
# monkey-patch — `time_machine`/`freezegun` is the preferred path. The 60-day
# suspension threshold is baked into `ParentalConsent.expires_at` at insertion
# (`_default_parental_consent_expires_at`), so the suspend task queries on
# `expires_at__lte=now()` directly — see §P13.
_REMINDER_AFTER_DAYS = 30


@shared_task(name="accounts.send_parental_consent_reminders")
def send_parental_consent_reminders() -> int:
    """Reminder dispatch — runs daily at 04:00 UTC (cf. path_advisor.celery beat).

    Returns the number of reminders sent so the task's success row in Celery flower /
    structlog is queryable. The DB write happens **after** the SMTP send completes:
    if mail dispatch raises, `reminder_sent_at` stays NULL and the next run retries.

    Story 1.4 review §P12 / §P13 / §P22:
      - materialise the queryset via `list()` (small N, < 10k rows/year) so we
        don't hold an open server-side cursor across SMTP latency
      - filter on `expires_at__gt=now()` directly instead of an in-loop `is_expired`
        check — keeps the reminder vs suspend boundary in SQL
      - move `consent.save(...)` inside the `try` so a save failure doesn't
        leave `sent` out of sync with the DB
    """
    now = timezone.now()
    pending = list(
        ParentalConsent.objects.filter(
            decision__isnull=True,
            reminder_sent_at__isnull=True,
            requested_at__lt=now - timedelta(days=_REMINDER_AFTER_DAYS),
            expires_at__gt=now,  # past-expiry rows are handled by the suspend task
        ).select_related("student")
    )

    sent = 0
    for consent in pending:
        try:
            ok = send_reminder_to_parent(consent)
            if not ok:
                # SMTP rejected — leave `reminder_sent_at` NULL so we retry tomorrow.
                continue
            consent.reminder_sent_at = timezone.now()
            consent.save(update_fields=["reminder_sent_at", "updated_at"])
            sent += 1
        except Exception:
            log.exception("parental_consent.reminder_failed", consent_id=consent.id)
            continue

    log.info("parental_consent.reminders_sent", count=sent)
    return sent


@shared_task(name="accounts.suspend_unresolved_parental_consents")
def suspend_unresolved_parental_consents() -> int:
    """Day-60 suspension dispatch — runs daily at 04:15 UTC.

    Sets the linked User to `SUSPENDED` (idempotently) and sends the final email
    to the child. The consent row stays in the DB so the `/decide/` endpoint can
    detect post-expiry calls and return 409 — and so an audit replay can be done
    months later.

    Story 1.4 review §P12 / §P13: query on `expires_at` (single source of truth)
    rather than recomputing `requested_at < now - 60d` — eliminates the
    `expires_at` vs `requested_at` divergence flagged by the reviewer.
    """
    pending = list(
        ParentalConsent.objects.filter(
            decision__isnull=True,
            expires_at__lte=timezone.now(),
        ).select_related("student")
    )

    suspended = 0
    for consent in pending:
        student = consent.student
        already_suspended = student.status == UserStatus.SUSPENDED
        suspend_for_unresolved_consent(consent=consent)
        if not already_suspended:
            try:
                send_expired_to_child(student)
            except Exception:
                log.exception("parental_consent.expired_email_failed", consent_id=consent.id)
            suspended += 1

    log.info("parental_consent.suspended", count=suspended)
    return suspended


@shared_task(name="accounts.notify_unconfirmed_granted_consents")
def notify_unconfirmed_granted_consents() -> int:
    """Reconciliation task — re-sends the "granted" email to children whose
    parent granted but whose notification never went out (SMTP failure during
    the synchronous `/decide/` POST). Story 1.4 review §P14.

    Idempotency: flips `consent.notification_sent_at` after a successful send so
    re-runs are no-ops. The column was added by migration `0004_parental_consent_*`.
    """
    pending = list(
        ParentalConsent.objects.filter(
            decision=ParentalConsentDecision.GRANTED,
            notification_sent_at__isnull=True,
        ).select_related("student")
    )

    sent = 0
    for consent in pending:
        try:
            ok = send_granted_to_child(consent.student)
            if not ok:
                continue
            consent.notification_sent_at = timezone.now()
            consent.save(update_fields=["notification_sent_at", "updated_at"])
            sent += 1
        except Exception:
            log.exception("parental_consent.grant_notify_failed", consent_id=consent.id)
            continue

    log.info("parental_consent.grant_notifications_sent", count=sent)
    return sent
