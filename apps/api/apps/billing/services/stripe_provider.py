"""Stripe implementation of the PaymentProvider interface — Story 5.1.

Uses the official `stripe` Python SDK. Keys come from settings (env-driven):
test-mode keys locally, live keys in prod, selected purely by configuration.
Only hosted Stripe Checkout is used — no card data ever touches Path-Advisor
(PCI SAQ-A).
"""

from __future__ import annotations

import stripe
from django.conf import settings

from apps.billing.services.provider import (
    CheckoutSession,
    InvalidWebhookSignature,
    PaymentProvider,
    WebhookEvent,
)


class StripeProvider(PaymentProvider):
    def __init__(self) -> None:
        self._client = stripe
        self._client.api_key = settings.STRIPE_SECRET_KEY
        self._price_id = settings.STRIPE_PRICE_ID_PREMIUM
        self._webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self._success_url = settings.STRIPE_CHECKOUT_SUCCESS_URL
        self._cancel_url = settings.STRIPE_CHECKOUT_CANCEL_URL

    def create_checkout_session(
        self, *, customer_email: str, client_reference_id: str
    ) -> CheckoutSession:
        session = self._client.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": self._price_id, "quantity": 1}],
            customer_email=customer_email,
            client_reference_id=client_reference_id,
            success_url=self._success_url,
            cancel_url=self._cancel_url,
        )
        return CheckoutSession(session_id=session["id"], checkout_url=session["url"])

    def handle_webhook(self, *, payload: bytes, signature_header: str) -> WebhookEvent:
        try:
            event = self._client.Webhook.construct_event(
                payload, signature_header, self._webhook_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            # ValueError → malformed payload; SignatureVerificationError → tampered/wrong secret.
            raise InvalidWebhookSignature(str(exc)) from exc
        return WebhookEvent(
            event_id=event["id"],
            event_type=event["type"],
            payload=dict(event),
        )

    def cancel_subscription(self, *, stripe_subscription_id: str) -> None:
        self._client.Subscription.cancel(stripe_subscription_id)

    def get_subscription_status(self, *, stripe_subscription_id: str) -> str:
        subscription = self._client.Subscription.retrieve(stripe_subscription_id)
        return subscription["status"]
