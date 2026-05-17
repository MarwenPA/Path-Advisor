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
