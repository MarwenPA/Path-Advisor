"""Story 8.1 — durable outbox for transactional email.

Why this exists: every sender in this codebase shared the same
"best-effort" contract — `except Exception → log.warning → return False` —
which means an email could be LOST SILENTLY on any SMTP hiccup (the exact
thing NFR-R4 / AC3 forbids). The outbox makes every send a durable row:
queued → sent, or failed WITH the error attached — visible, queryable, and
replayable (`retry_failed_emails`). Losing an email now requires deleting
a row, not just a dropped connection.

Privacy note (the app serves minors): rows hold recipient addresses and
template contexts that may embed sensitive URLs (invitation/consent
tokens). Deliberately **no API surface at all** — no serializer, no view;
reads happen via ORM/shell only, and `prune_email_outbox` bounds retention
the same way `prune_rum_vitals` does for telemetry.
"""

from __future__ import annotations

from django.db import models


class OutboxStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SENT = "sent", "Sent"
    # Terminal only after retries are exhausted or on a non-retryable
    # (programming) error — never a silent state: `last_error` is filled and
    # the task logs at ERROR level.
    FAILED = "failed", "Failed"


class EmailOutbox(models.Model):
    to = models.EmailField()
    #: Django app label owning the templates, e.g. "family" — the task
    #: renders `<template_app>/<template_base>{_subject.txt,.txt,.html}`,
    #: the exact convention every existing sender already uses.
    template_app = models.CharField(max_length=64)
    template_base = models.CharField(max_length=128)
    #: MUST stay JSON-serializable — the row has to survive a process
    #: restart, so live model instances are not allowed here.
    context = models.JSONField(default=dict)
    status = models.CharField(
        max_length=10, choices=OutboxStatus.choices, default=OutboxStatus.QUEUED
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "email_outbox"
        indexes = [
            # `retry_failed_emails` scans by status; ops dashboards by day.
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"[{self.status}] {self.template_app}/{self.template_base} → {self.to}"
