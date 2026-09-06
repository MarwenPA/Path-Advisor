"""Billing models — Story 5.1 (`StripeEvent`) + Story 5.2 (`Subscription`).

`StripeEvent` is the idempotency ledger for inbound Stripe webhooks: every
event id Stripe delivers is recorded exactly once (unique `stripe_event_id`).

`Subscription` holds the B2C tier state (free / premium) for a user, driven by
the Stripe webhook lifecycle. `is_active_now` is grace-aware: a `past_due`
subscription keeps premium until `grace_until` (7-day dunning window).

Data classification: Stripe object ids only (no card data — PCI SAQ-A).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.ids import generate_id


def _new_event_id() -> str:
    return generate_id("evt")


def _new_subscription_id() -> str:
    return generate_id("sub")


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


class Subscription(models.Model):
    """B2C subscription tier state for a user — Story 5.2."""

    class Tier(models.TextChoices):
        FREE = "free", "Freemium"
        PREMIUM = "premium", "Premium"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELLED = "cancelled", "Cancelled"

    id = models.CharField(
        primary_key=True, max_length=64, default=_new_subscription_id, editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription"
    )
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    current_period_end = models.DateTimeField(null=True, blank=True)
    # Set when status → past_due: premium stays live until this instant (7-day
    # dunning grace). Cleared on recovery.
    grace_until = models.DateTimeField(null=True, blank=True)
    # Story 5.3 — set when the user requests cancellation: the subscription
    # keeps premium access until `current_period_end`, then Stripe's
    # `customer.subscription.deleted` (5.2) flips tier→free/status→cancelled.
    # Distinct from an immediate cancel (merge-on-second-checkout, RGPD
    # pre_delete signal) which never sets this flag.
    cancel_at_period_end = models.BooleanField(default=False)
    # Story 6.4 — set when this subscription was purchased by a linked
    # PARENT on the student's behalf rather than by the student themselves.
    # `SET_NULL` on delete: losing the payer's account must never take down
    # the beneficiary's (already-paid-for) premium access.
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions_paid_for",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_subscriptions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id}: {self.tier}/{self.status}"

    @property
    def is_active_now(self) -> bool:
        """True iff this subscription currently grants premium access.

        `active` premium always grants; `past_due` premium grants only within
        the grace window (`grace_until > now`).
        """
        if self.tier != self.Tier.PREMIUM:
            return False
        if self.status == self.Status.ACTIVE:
            return True
        if self.status == self.Status.PAST_DUE:
            return self.grace_until is not None and self.grace_until > timezone.now()
        return False
