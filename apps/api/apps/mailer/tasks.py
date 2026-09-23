"""Story 8.1 — Celery delivery with exponential retry, no silent loss.

Retry policy is explicit rather than `autoretry_for`: on final exhaustion
`autoretry_for` re-raises and would leave the outbox row in limbo — here
every terminal path WRITES the row's fate first.

`_EMAIL_RETRY_EXC` is the canonical retryable list, hoisted from
`accounts/tasks.py` (Story 1.11 post-review): infrastructure failures
retry, programming bugs (TemplateDoesNotExist, KeyError in a template)
fail fast — retrying a bug 8 times just delays the alert.
"""

from __future__ import annotations

from smtplib import SMTPException

import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailOutbox, OutboxStatus

log = structlog.get_logger(__name__)

#: Canonical retryable email exceptions (single source — `accounts.tasks`
#: imports this rather than keeping its own copy).
EMAIL_RETRY_EXC = (SMTPException, ConnectionError, TimeoutError, OSError)

#: 30s, 60s, 120s, ... capped at 1h. 8 attempts ≈ half a day of coverage —
#: enough to ride out an SMTP outage without turning the queue into a
#: permanent hammer.
MAX_RETRIES = 8
BACKOFF_BASE_SECONDS = 30
BACKOFF_CAP_SECONDS = 3600


def _render_and_send(row: EmailOutbox) -> None:
    prefix = f"{row.template_app}/{row.template_base}"
    subject = render_to_string(f"{prefix}_subject.txt", row.context).strip()
    body_txt = render_to_string(f"{prefix}.txt", row.context)
    body_html = render_to_string(f"{prefix}.html", row.context)
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
    try:
        row = EmailOutbox.objects.get(pk=outbox_id)
    except EmailOutbox.DoesNotExist:
        # Pruned or rolled back before the worker picked it up — nothing to do.
        log.warning("mailer.outbox_row_missing", outbox_id=outbox_id)
        return "missing"

    if row.status == OutboxStatus.SENT:
        # acks_late + worker crash can redeliver a completed task; sending
        # twice is worse than a no-op here.
        return "already-sent"

    row.attempts += 1

    try:
        _render_and_send(row)
    except EMAIL_RETRY_EXC as exc:
        row.last_error = f"{type(exc).__name__}: {exc}"
        row.save(update_fields=["attempts", "last_error"])
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
            row.save(update_fields=["status"])
            # ERROR, not warning: this is the "no silent loss" contract —
            # the row is terminal and someone must look at it
            # (`retry_failed_emails` replays once the cause is fixed).
            log.error(
                "mailer.email_failed_permanently",
                outbox_id=row.pk,
                template=f"{row.template_app}/{row.template_base}",
                attempts=row.attempts,
                error=row.last_error,
            )
            return "failed"
        countdown = min(BACKOFF_BASE_SECONDS * 2 ** (row.attempts - 1), BACKOFF_CAP_SECONDS)
        raise self.retry(exc=exc, countdown=countdown) from exc
    except Exception as exc:
        # Programming bug (missing template, bad context key): retrying
        # cannot fix it — fail fast and loud instead.
        row.status = OutboxStatus.FAILED
        row.last_error = f"{type(exc).__name__}: {exc}"
        row.save(update_fields=["attempts", "status", "last_error"])
        log.error(
            "mailer.email_failed_nonretryable",
            outbox_id=row.pk,
            template=f"{row.template_app}/{row.template_base}",
            error=row.last_error,
        )
        return "failed"

    row.status = OutboxStatus.SENT
    row.sent_at = timezone.now()
    row.last_error = ""
    row.save(update_fields=["attempts", "status", "sent_at", "last_error"])
    log.info(
        "mailer.email_sent",
        outbox_id=row.pk,
        template=f"{row.template_app}/{row.template_base}",
        attempts=row.attempts,
    )
    return "sent"
