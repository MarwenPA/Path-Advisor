"""Payment provider abstraction — Story 5.1 (NFR-I1).

The rest of the billing code depends only on this `PaymentProvider` interface,
never on a concrete SDK. Swapping test ↔ prod (or, in theory, Stripe ↔ another
processor) is a configuration change, not a code change — mirroring the storages
(MinIO/S3) and OCR (Tesseract/Mindee) abstractions elsewhere in the codebase.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CheckoutSession:
    """Result of creating a hosted checkout session."""

    session_id: str
    checkout_url: str


@dataclass(frozen=True)
class WebhookEvent:
    """A verified inbound webhook event."""

    event_id: str
    event_type: str
    payload: dict[str, Any]


class PaymentProvider(abc.ABC):
    """Interface every payment backend must implement (NFR-I1)."""

    @abc.abstractmethod
    def create_checkout_session(
        self,
        *,
        customer_email: str,
        client_reference_id: str,
        metadata: dict[str, str] | None = None,
    ) -> CheckoutSession:
        """Create a hosted checkout session for the premium plan and return its URL.

        `metadata` (Story 6.4) — Stripe echoes this dict back verbatim on
        `checkout.session.completed`; used to carry `paid_by_user_id` when a
        parent pays on a linked child's behalf (`client_reference_id` stays
        the beneficiary — never the payer — so `SubscriptionService.
        _resolve_user` needs no special-casing).
        """

    @abc.abstractmethod
    def handle_webhook(self, *, payload: bytes, signature_header: str) -> WebhookEvent:
        """Verify the signature and return the parsed event. Raise on invalid signature."""

    @abc.abstractmethod
    def cancel_subscription(self, *, stripe_subscription_id: str) -> None:
        """Cancel a subscription IMMEDIATELY at the provider.

        Used by merge-on-second-checkout and the RGPD `pre_delete` signal —
        both need the subscription gone now, not at period end. User-initiated
        cancellation (Story 5.3 AC3) must use `schedule_cancellation` instead.
        """

    @abc.abstractmethod
    def schedule_cancellation(self, *, stripe_subscription_id: str) -> None:
        """Schedule a subscription to cancel AT THE END of its current period.

        Story 5.3 AC3 — the user keeps premium access until
        `current_period_end`; Stripe fires `customer.subscription.deleted`
        (already handled, Story 5.2) once the period actually ends.
        """

    @abc.abstractmethod
    def get_subscription_status(self, *, stripe_subscription_id: str) -> str:
        """Return the provider-side status string for a subscription."""


class InvalidWebhookSignature(Exception):
    """Raised by a provider when a webhook signature fails verification."""
