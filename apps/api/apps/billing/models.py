"""Billing models — Story 5.1 (Stripe integration foundation).

`StripeEvent` is the idempotency ledger for inbound Stripe webhooks: every
event id Stripe delivers is recorded exactly once. A re-delivered event (Stripe
retries until it gets a 2xx) is detected via the unique `stripe_event_id` and
processed as a no-op.

The `Subscription` / `Invoice` models and the `is_premium` tier flag are
introduced in Story 5.2 (tiers & gating) — this story deliberately only lands
the plumbing (provider abstraction + webhook receipt + idempotency).

Data classification: Stripe object ids only (no card data — PCI SAQ-A).
"""

from __future__ import annotations

from django.db import models

from apps.core.ids import generate_id


def _new_event_id() -> str:
    return generate_id("evt")


class StripeEvent(models.Model):
    """One row per Stripe webhook event received, for idempotent processing."""

    id = models.CharField(primary_key=True, max_length=64, default=_new_event_id, editable=False)
    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "billing_stripe_events"
        ordering = ["-received_at"]

    def __str__(self) -> str:
        return f"{self.event_type} ({self.stripe_event_id})"
