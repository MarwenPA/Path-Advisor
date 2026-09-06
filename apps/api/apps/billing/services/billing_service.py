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

from apps.audit.decorators import audit_action, record_audit
from apps.audit.models import AuditResult
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
        metadata_from=lambda kwargs, ret: {
            "beneficiary_user_id": (kwargs.get("beneficiary") or kwargs["user"]).id,
        },
    )
    def create_checkout_session(self, *, user, beneficiary=None) -> CheckoutSession:
        """`beneficiary` (Story 6.4) — the user whose tier upgrades once this
        checkout completes. `None` (the default, every pre-6.4 call site)
        means "self-checkout": `user` pays and benefits. When a linked
        `PARENT` pays for their child, `user` is the parent (Stripe customer,
        audit actor) and `beneficiary` is the child — `client_reference_id`
        is always the beneficiary so the webhook activates the right
        `Subscription` row without any special-casing.
        """
        target = beneficiary or user
        metadata = {"paid_by_user_id": user.id} if beneficiary is not None else None
        try:
            return self._provider.create_checkout_session(
                customer_email=user.email,
                client_reference_id=target.id,
                metadata=metadata,
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

        Dedicated audit path (code review, 2026-08): any audit row written
        *inside* the `with transaction.atomic()` block below (e.g. the
        `rls.bypass_used` row `SubscriptionService.apply_event` emits via
        `bypass_rls`) is rolled back along with everything else if processing
        raises — `record_audit()` intentionally joins the caller's open
        transaction (Story 1.13 policy). That would silently erase the only
        trace of a failed webhook attempt. The `except` clause below runs
        strictly AFTER the `with` block has unwound and rolled back — the
        connection is back to a clean state there, so this `record_audit()`
        call starts and commits its own fresh transaction, independent of the
        failure, guaranteeing at least one durable audit row per failed
        attempt.
        """
        event = self._provider.handle_webhook(payload=payload, signature_header=signature_header)

        try:
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

                handled = self._process_event(event)
                # Code-review fix (2026-08): only stamp `processed_at` when a
                # handler actually existed for this event type. Previously EVERY
                # event was marked processed regardless, including types with no
                # handler yet — Stripe never redelivers a 200'd event, so an
                # event type added to `SubscriptionService.apply_event` in a
                # later story would find all of its historical occurrences
                # already (falsely) marked "processed" and permanently lose
                # them. Leaving `processed_at=NULL` for unhandled types keeps
                # them dedup'd (the ledger row still exists) but reprocessable
                # by a future backfill once a handler lands.
                if handled:
                    row.processed_at = timezone.now()
                    row.save(update_fields=["processed_at"])
        except Exception as exc:
            # Runs outside the (now rolled-back) atomic block — see docstring.
            record_audit(
                action="billing.webhook_processing_failed",
                result=AuditResult.FAILURE,
                subject_id=event.event_id,
                metadata={"event_type": event.event_type, "error_type": exc.__class__.__name__},
            )
            raise
        return event

    def _process_event(self, event: WebhookEvent) -> bool:
        """Dispatch subscription lifecycle events to the SubscriptionService (5.2).

        Returns True iff a handler existed for `event.event_type` — see the
        `processed_at` comment in `record_webhook_event` for why this matters.
        """
        from apps.billing.services.subscription_service import SubscriptionService

        data_object = (event.payload.get("data") or {}).get("object") or {}
        return SubscriptionService.apply_event(event_type=event.event_type, obj=data_object)


__all__ = ["BillingService", "InvalidWebhookSignature"]
