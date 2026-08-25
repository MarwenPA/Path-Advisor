"""Billing service layer — Story 5.1.

Business logic lives here (never in views): create a checkout session for the
current user, and record inbound webhook events idempotently. Provider errors
are wrapped as `PaymentProviderError` (RFC 7807) so the API never leaks a bare
500 and no partial local state is created on failure (degraded-mode fallback).
"""

from __future__ import annotations

import stripe
import structlog
from django.db import transaction
from django.utils import timezone

from apps.audit.decorators import audit_action
from apps.billing.models import StripeEvent
from apps.billing.services import get_payment_provider
from apps.billing.services.provider import CheckoutSession, InvalidWebhookSignature, WebhookEvent
from apps.core.exceptions import PaymentProviderError

log = structlog.get_logger(__name__)


class BillingService:
    def __init__(self) -> None:
        self._provider = get_payment_provider()

    @audit_action(
        "billing.checkout_session_created",
        subject_from=lambda kwargs, ret: kwargs["user"].id,
    )
    def create_checkout_session(self, *, user) -> CheckoutSession:
        try:
            return self._provider.create_checkout_session(
                customer_email=user.email,
                client_reference_id=user.id,
            )
        except stripe.error.StripeError as exc:
            # Only provider-side failures become a 502 (degraded mode). Any other
            # exception is a real bug and must propagate as a 500 (surfaced to
            # Sentry) rather than be masked as a transient payment outage.
            log.error("billing.checkout_session_failed", error=str(exc))
            raise PaymentProviderError() from exc

    def record_webhook_event(self, *, payload: bytes, signature_header: str) -> WebhookEvent:
        """Verify + persist a webhook event idempotently. Raises InvalidWebhookSignature.

        The whole record-and-process step runs in one transaction with a row
        lock so concurrent re-deliveries of the same event cannot both process
        it: the second delivery blocks on `select_for_update` until the first
        commits, then sees `processed_at` set and short-circuits. If processing
        raises, the transaction rolls back — including a freshly-created ledger
        row — so no partial state survives (Stripe will retry).
        """
        event = self._provider.handle_webhook(payload=payload, signature_header=signature_header)

        # Persist only non-PII envelope fields — the full Stripe event body
        # (which for e.g. checkout.session.completed carries customer_details
        # PII) is intentionally NOT stored (PCI SAQ-A + data classification).
        with transaction.atomic():
            StripeEvent.objects.get_or_create(
                stripe_event_id=event.event_id,
                defaults={"event_type": event.event_type, "payload": {}},
            )
            row = StripeEvent.objects.select_for_update().get(stripe_event_id=event.event_id)
            if row.processed_at is not None:
                # Re-delivery of an already-processed event → no-op (idempotent).
                return event

            self._process_event(event)
            row.processed_at = timezone.now()
            row.save(update_fields=["processed_at"])
        return event

    def _process_event(self, event: WebhookEvent) -> None:
        """Dispatch by event type. Full subscription activation lands in Story 5.3."""
        if event.event_type == "checkout.session.completed":
            log.info("billing.checkout_completed", event_id=event.event_id)
        # Other event types are recorded but not yet acted upon (5.2 / 5.3).


__all__ = ["BillingService", "InvalidWebhookSignature"]
