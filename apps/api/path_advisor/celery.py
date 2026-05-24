"""Celery application — autodiscovers tasks and registers the audit beat schedule."""

import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_postrun, task_prerun

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")

app = Celery("path_advisor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Audit maintenance — monthly archival + integrity check (Story 1.13 §AC6).
app.conf.beat_schedule = {
    "audit-archive-old-logs": {
        "task": "audit.archive_old_logs",
        "schedule": crontab(day_of_month="1", hour=3, minute=0),
    },
    "audit-verify-chain-integrity": {
        "task": "audit.verify_chain_integrity",
        "schedule": crontab(day_of_month="2", hour=4, minute=0),
    },
    # Story 1.4 parental-consent lifecycle. Daily windows are deliberate: the queries
    # are pull-based on `requested_at + N days`, so missing a day just delays affected
    # rows by 24h — there's no debt accumulation.
    "parental-consent-send-reminders": {
        "task": "accounts.send_parental_consent_reminders",
        "schedule": crontab(hour=4, minute=0),
    },
    "parental-consent-suspend-unresolved": {
        "task": "accounts.suspend_unresolved_parental_consents",
        "schedule": crontab(hour=4, minute=15),
    },
    # Story 1.4 review §P14: reconciliation task — re-sends the "granted" child
    # email for rows where the synchronous /decide/ POST hit an SMTP failure.
    # Runs hourly because the unhappy path is rare and we want to close the gap
    # quickly (parents may already have moved on if the child says "I haven't
    # got the confirmation").
    "parental-consent-notify-unconfirmed-granted": {
        "task": "accounts.notify_unconfirmed_granted_consents",
        "schedule": crontab(minute=20),
    },
    # Story 1.11 — expire les exports RGPD au-delà de GDPR_EXPORT_VALIDITY_DAYS (default 7).
    "gdpr-expire-old-exports": {
        "task": "gdpr.expire_old_exports",
        "schedule": crontab(hour=4, minute=30),
    },
    # Story 1.12 — hard-delete cascade for account-deletion requests past their
    # 30-day grace window. 03:45 Paris = 02:45 UTC (Celery beat default TZ).
    # Slotted 15 minutes after the audit archival / GDPR-export expiry tasks so
    # the daily ordering is deterministic for incident debugging.
    "accounts-sweep-account-deletions": {
        "task": "accounts.sweep_account_deletions",
        "schedule": crontab(hour=2, minute=45),
    },
}


# Audit thread-local hygiene: prevent actor/tenant context from leaking across
# tasks when a worker thread is reused. Without this, a task triggered by a
# view (which sets request_context) followed by a scheduled task (which does
# not) would audit the scheduled task as the previous user. Story 1.13 review.
@task_prerun.connect
def _clear_audit_context_before_task(**kwargs):
    from apps.core import request_context

    request_context.clear()


@task_postrun.connect
def _clear_audit_context_after_task(**kwargs):
    from apps.core import request_context

    request_context.clear()
