"""Unit tests for the payment provider abstraction + StripeProvider — Story 5.1."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import stripe

from apps.billing.services import get_payment_provider
from apps.billing.services.provider import (
    CheckoutSession,
    InvalidWebhookSignature,
    PaymentProvider,
)
from apps.billing.services.stripe_provider import StripeProvider


def test_factory_returns_configured_provider():
    provider = get_payment_provider()
    assert isinstance(provider, PaymentProvider)
    assert isinstance(provider, StripeProvider)


def test_create_checkout_session_uses_hosted_checkout():
    provider = StripeProvider()
    fake_session = {"id": "cs_test_123", "url": "https://checkout.stripe.com/c/pay/cs_test_123"}
    with patch.object(stripe.checkout.Session, "create", return_value=fake_session) as create:
        result = provider.create_checkout_session(
            customer_email="eleve@example.com", client_reference_id="usr_1"
        )
    assert isinstance(result, CheckoutSession)
    assert result.session_id == "cs_test_123"
    assert result.checkout_url.startswith("https://checkout.stripe.com/")
    # Hosted subscription checkout, no raw card fields.
    _, kwargs = create.call_args
    assert kwargs["mode"] == "subscription"
    assert kwargs["client_reference_id"] == "usr_1"


def test_handle_webhook_valid_signature_returns_event():
    provider = StripeProvider()
    fake_event = {"id": "evt_1", "type": "checkout.session.completed", "data": {}}
    with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
        event = provider.handle_webhook(payload=b"{}", signature_header="t=1,v1=abc")
    assert event.event_id == "evt_1"
    assert event.event_type == "checkout.session.completed"


def test_handle_webhook_bad_signature_raises():
    provider = StripeProvider()
    with (
        patch.object(
            stripe.Webhook,
            "construct_event",
            side_effect=stripe.error.SignatureVerificationError("bad", "sig"),
        ),
        pytest.raises(InvalidWebhookSignature),
    ):
        provider.handle_webhook(payload=b"{}", signature_header="bad")


def test_handle_webhook_malformed_payload_raises():
    provider = StripeProvider()
    with (
        patch.object(stripe.Webhook, "construct_event", side_effect=ValueError("bad json")),
        pytest.raises(InvalidWebhookSignature),
    ):
        provider.handle_webhook(payload=b"not-json", signature_header="t=1")
