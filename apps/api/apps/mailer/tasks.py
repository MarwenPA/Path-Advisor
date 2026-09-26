"""Story 8.1 — Celery delivery with exponential retry, no silent loss.

Retry policy is explicit rather than `autoretry_for`: on final exhaustion
`autoretry_for` re-raises and would leave the outbox row in limbo — here
every terminal path WRITES the row's fate first.

`_EMAIL_RETRY_EXC` is the canonical retryable list, hoisted from
`accounts/tasks.py` (Story 1.11 post-review): infrastructure failures
retry, programming bugs (TemplateDoesNotExist, KeyError in a template)
fail fast — retrying a bug 8 times just delays the alert.

Review fixes (revue Epic 8, 2026-09-26):
- P1-2a: delivery starts with a compare-and-swap claim (QUEUED → SENDING)
  so concurrent executions of the same row (double enqueue, Redis
  visibility-timeout redelivery, double `retry_failed_emails`) no-op
  instead of double-sending a minor.
- P1-1: `sweep_stale_outbox` (beat) re-enqueues rows whose enqueue hook
  never reached the broker and rows stuck SENDING after a worker crash —
  the two "silent loss" holes.
- P2-11: category emails re-check the opt-out at DELIVERY time.
- P2-6: the legal footer (incl. the signed unsubscribe token) is built at
  RENDER time from `notification_user_id`/`notification_category` — no
  capability URL is persisted in `context` anymore.
"""

from __future__ import annotations

import os
from datetime import timedelta
from smtplib import SMTPException

import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailOutbox, OutboxStatus

log = structlog.get_logger(__name__)

#: Canonical retryable email exceptions (single source — `accounts.tasks`
#: imports this rather than keeping its own copy).
EMAIL_RETRY_EXC = (SMTPException, ConnectionError, TimeoutError, OSError)

#: 30s, 60s, 120s, ... capped at 1h. Total coverage across the 8 retries is
#: 30+60+120+240+480+960+1920+3600 ≈ **2 h 04** (the first version claimed
#: "half a day" — review fix, the ops expectation must be honest). An SMTP
#: outage longer than ~2 h flips rows to FAILED (loud, replayable via
#: `retry_failed_emails`).
MAX_RETRIES = 8
BACKOFF_BASE_SECONDS = 30
BACKOFF_CAP_SECONDS = 3600

#: Sweeper grace periods (review fix P1-1). A row QUEUED with attempts=0
#: older than this was never picked up (its on_commit hook failed / the
#: process died between commit and hook): safe to re-enqueue fast. A row
#: QUEUED with attempts>0 is usually WAITING for its retry ETA (max
#: countdown 3600 s) — only sweep it past that horizon. A row stuck SENDING
#: means a worker crashed mid-send: re-queueing is a deliberate
#: at-least-once choice (the SMTP-accept→UPDATE window is irreducible;
#: better a rare duplicate than a silent loss) and is logged loudly.
STALE_QUEUED_FRESH = timedelta(minutes=15)
STALE_QUEUED_RETRYING = timedelta(minutes=70)
STALE_SENDING = timedelta(minutes=30)
SWEEP_BATCH = 500


def _site_url() -> str:
    return os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")


def _notification_footer(row: EmailOutbox) -> dict[str, str]:
    """Legal footer for category emails, built at render time (P2-6).

    Imports stay local: `notifications.services` imports `mailer.service`,
    so a module-level import here would be circular.
    """
    from apps.notifications.models import NotificationCategory
    from apps.notifications.tokens import make_unsubscribe_token

    token = make_unsubscribe_token(row.notification_user_id, row.notification_category)
    return {
        "manage_notifications_url": f"{_site_url()}/parametres/notifications",
        "unsubscribe_url": f"{_site_url()}/desinscription/{token}",
        "category_label": NotificationCategory(row.notification_category).label,
    }


def _render_and_send(row: EmailOutbox) -> None:
    context = dict(row.context)
    if row.notification_user_id and row.notification_category:
        context.update(_notification_footer(row))
    prefix = f"{row.template_app}/{row.template_base}"
    subject = render_to_string(f"{prefix}_subject.txt", context).strip()
    body_txt = render_to_string(f"{prefix}.txt", context)
    body_html = render_to_string(f"{prefix}.html", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[row.to],
    )
    msg.attach_alternative(body_html, "text/html")
    msg.send(fail_silently=False)


@shared_task(bind=True, name="mailer.deliver_email", acks_late=True, max_retries=MAX_RETRIES)
def deliver_email(self, outbox_id: int) -> str:
    # CAS claim (review fix P1-2a): exactly one execution may move the row
    # QUEUED → SENDING. A concurrent duplicate updates 0 rows and no-ops —
    # this closes both the double-enqueue and the visibility-timeout
    # redelivery double-send windows.
    now = timezone.now()
    claimed = EmailOutbox.objects.filter(pk=outbox_id, status=OutboxStatus.QUEUED).update(
        status=OutboxStatus.SENDING, attempts=F("attempts") + 1, updated_at=now
    )
    if not claimed:
        try:
            status = EmailOutbox.objects.values_list("status", flat=True).get(pk=outbox_id)
        except EmailOutbox.DoesNotExist:
            # Pruned or rolled back before the worker picked it up.
            log.warning("mailer.outbox_row_missing", outbox_id=outbox_id)
            return "missing"
        # SENT → duplicate delivery of a completed task; SENDING → another
        # worker holds it right now (or crashed mid-send — the sweeper
        # re-queues stale SENDING rows); FAILED/SKIPPED → terminal.
        return f"not-claimed:{status}"

    row = EmailOutbox.objects.get(pk=outbox_id)

    # Opt-out re-check at DELIVERY time (review fix P2-11): a student who
    # unsubscribed between enqueue and delivery (retry window ≈ 2 h during
    # an outage) must not receive the category email.
    if row.notification_user_id and row.notification_category:
        from apps.notifications.models import is_enabled

        if not is_enabled(row.notification_user_id, row.notification_category):
            row.status = OutboxStatus.SKIPPED
            row.updated_at = timezone.now()
            row.save(update_fields=["status", "updated_at"])
            log.info(
                "mailer.email_skipped_opted_out",
                outbox_id=row.pk,
                category=row.notification_category,
            )
            return "skipped-opted-out"

    try:
        _render_and_send(row)
    except EMAIL_RETRY_EXC as exc:
        row.last_error = f"{type(exc).__name__}: {exc}"
        # Exhaustion is checked BEFORE calling retry. The first version
        # caught MaxRetriesExceededError around `self.retry(exc=exc, ...)` —
        # dead code: with `exc` passed, Celery re-raises the ORIGINAL
        # exception at exhaustion, so the FAILED transition never fired and
        # an exhausted row stayed QUEUED forever, invisible to
        # `retry_failed_emails` (which scans FAILED). The story 8.1
        # migration agent caught it — my own test had masked the bug by
        # patching `retry` to raise MaxRetriesExceededError, testing my
        # assumption instead of Celery's real semantics.
        if self.request.retries >= self.max_retries:
            row.status = OutboxStatus.FAILED
            row.updated_at = timezone.now()
            row.save(update_fields=["status", "last_error", "updated_at"])
            # ERROR, not warning: this is the "no silent loss" contract —
            # the row is terminal and someone must look at it
            # (`retry_failed_emails` replays once the cause is fixed).
            # Only the exception TYPE goes to the log stream (review fix
            # P2-6c: str(SMTPRecipientsRefused) embeds the recipient
            # address); the full detail stays on the row.
            log.error(
                "mailer.email_failed_permanently",
                outbox_id=row.pk,
                template=f"{row.template_app}/{row.template_base}",
                attempts=row.attempts,
                error_type=type(exc).__name__,
            )
            return "failed"
        # Back to QUEUED while waiting for the retry ETA — the next
        # attempt's CAS needs it, and the sweeper knows a QUEUED row with
        # attempts>0 is waiting, not lost (70 min grace > max countdown).
        row.status = OutboxStatus.QUEUED
        row.updated_at = timezone.now()
        row.save(update_fields=["status", "last_error", "updated_at"])
        countdown = min(BACKOFF_BASE_SECONDS * 2 ** (row.attempts - 1), BACKOFF_CAP_SECONDS)
        raise self.retry(exc=exc, countdown=countdown) from exc
    except Exception as exc:
        # Programming bug (missing template, bad context key): retrying
        # cannot fix it — fail fast and loud instead.
        row.status = OutboxStatus.FAILED
        row.last_error = f"{type(exc).__name__}: {exc}"
        row.updated_at = timezone.now()
        row.save(update_fields=["status", "last_error", "updated_at"])
        log.error(
            "mailer.email_failed_nonretryable",
            outbox_id=row.pk,
            template=f"{row.template_app}/{row.template_base}",
            error_type=type(exc).__name__,
        )
        return "failed"

    row.status = OutboxStatus.SENT
    row.sent_at = timezone.now()
    row.updated_at = row.sent_at
    row.last_error = ""
    row.save(update_fields=["status", "sent_at", "last_error", "updated_at"])
    log.info(
        "mailer.email_sent",
        outbox_id=row.pk,
        template=f"{row.template_app}/{row.template_base}",
        attempts=row.attempts,
    )
    return "sent"


@shared_task(name="mailer.sweep_stale_outbox")
def sweep_stale_outbox() -> dict[str, int]:
    """Beat task (review fix P1-1): no outbox row may be lost silently.

    Three populations, three graces (see the module constants):
    - QUEUED, attempts=0, older than 15 min → the enqueue hook never made
      it to the broker; re-enqueue (the CAS makes a duplicate harmless).
    - QUEUED, attempts>0, no transition for 70 min → its retry ETA message
      was lost (broker flush); re-enqueue.
    - SENDING, no transition for 30 min → worker crashed mid-send;
      re-queue LOUDLY (deliberate at-least-once — a rare duplicate beats a
      silent loss; the irreducible window is SMTP-accept → status UPDATE).
    """
    now = timezone.now()
    counts = {"requeued_fresh": 0, "requeued_retrying": 0, "requeued_sending": 0}

    fresh = EmailOutbox.objects.filter(
        status=OutboxStatus.QUEUED, attempts=0, created_at__lt=now - STALE_QUEUED_FRESH
    ).values_list("pk", flat=True)[:SWEEP_BATCH]
    for pk in fresh:
        deliver_email.delay(pk)
        counts["requeued_fresh"] += 1

    retrying = EmailOutbox.objects.filter(
        status=OutboxStatus.QUEUED,
        attempts__gt=0,
        updated_at__lt=now - STALE_QUEUED_RETRYING,
    ).values_list("pk", flat=True)[:SWEEP_BATCH]
    for pk in retrying:
        deliver_email.delay(pk)
        counts["requeued_retrying"] += 1

    stuck = list(
        EmailOutbox.objects.filter(
            status=OutboxStatus.SENDING, updated_at__lt=now - STALE_SENDING
        ).values_list("pk", flat=True)[:SWEEP_BATCH]
    )
    for pk in stuck:
        # Conditional flip back to QUEUED, then re-enqueue.
        flipped = EmailOutbox.objects.filter(pk=pk, status=OutboxStatus.SENDING).update(
            status=OutboxStatus.QUEUED, updated_at=now
        )
        if flipped:
            log.error("mailer.sending_stale_requeued", outbox_id=pk)
            deliver_email.delay(pk)
            counts["requeued_sending"] += 1

    if any(counts.values()):
        log.warning("mailer.sweep_stale_outbox", **counts)
    return counts


@shared_task(name="mailer.prune_email_outbox")
def prune_email_outbox_task(days: int = 90) -> int:
    """Beat wrapper for the retention policy (review fix P0-2): the public
    RGPD page promises 90 days — a management command nobody schedules is
    not a retention policy."""
    from .retention import prune_email_outbox

    deleted = prune_email_outbox(days=days)
    log.info("mailer.pruned_email_outbox", deleted=deleted, days=days)
    return deleted
