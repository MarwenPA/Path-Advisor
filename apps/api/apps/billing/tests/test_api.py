"""API tests for billing endpoints — Story 5.1."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import stripe
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.billing.models import StripeEvent
from apps.billing.services.provider import (
    CheckoutSession,
    InvalidWebhookSignature,
    WebhookEvent,
)
from apps.core.rls import bypass_rls

pytestmark = pytest.mark.django_db


def _make_user(*, active: bool = True) -> User:
    # `users` has FORCE RLS (Story 1.8) — test setup writes go through the
    # sanctioned bypass helper, mirroring how the app creates system rows.
    with bypass_rls(reason="test_setup.create_billing_user"):
        return User.objects.create_user(
            email=f"billing_{'active' if active else 'inactive'}@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE if active else UserStatus.EMAIL_UNVERIFIED,
            email_verified_at=timezone.now() if active else None,
        )


# --- checkout-session -------------------------------------------------------


def test_checkout_session_requires_authentication():
    url = reverse("billing:checkout-session")
    resp = APIClient().post(url)
    assert resp.status_code in (401, 403)


def test_checkout_session_blocked_for_not_fully_active_user():
    user = _make_user(active=False)
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post(reverse("billing:checkout-session"))
    assert resp.status_code == 403


def test_checkout_session_returns_url_for_active_user():
    user = _make_user()
    client = APIClient()
    client.force_authenticate(user=user)
    fake = CheckoutSession(session_id="cs_1", checkout_url="https://checkout.stripe.com/c/cs_1")
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.create_checkout_session",
        return_value=fake,
    ):
        resp = client.post(reverse("billing:checkout-session"))
    assert resp.status_code == 201
    assert resp.data["checkout_url"] == "https://checkout.stripe.com/c/cs_1"


def test_checkout_session_provider_failure_is_rfc7807():
    user = _make_user()
    client = APIClient()
    client.force_authenticate(user=user)
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.create_checkout_session",
        side_effect=stripe.error.APIConnectionError("stripe down"),
    ):
        resp = client.post(reverse("billing:checkout-session"))
    assert resp.status_code == 502
    # RFC 7807-shaped body (DRF APIView renders the problem dict as
    # application/json; the body carries the machine-readable `type`/`title`).
    assert resp.data["type"].endswith("/payment-provider-unavailable")
    assert resp.data["title"]
    assert resp.data["status"] == 502
    # No partial state persisted on failure.
    assert StripeEvent.objects.count() == 0


# --- webhook ----------------------------------------------------------------


def test_webhook_rejects_bad_signature():
    url = reverse("stripe-webhook")
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
        side_effect=InvalidWebhookSignature("bad"),
    ):
        resp = APIClient().post(url, data=b"{}", content_type="application/json")
    assert resp.status_code == 400
    assert StripeEvent.objects.count() == 0


def test_webhook_bad_signature_writes_audit_row():
    """Code-review fix (2026-08): the HMAC signature is this endpoint's sole
    auth proof — an invalid one is an auth failure and must be audited like
    `auth.login_failed`, so a forged/replayed attempt leaves a trace."""
    from apps.audit.models import AuditLog, AuditResult

    url = reverse("stripe-webhook")
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
        side_effect=InvalidWebhookSignature("bad"),
    ):
        APIClient().post(
            url, data=b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=bad"
        )
    assert AuditLog.objects.filter(
        action="billing.webhook_signature_invalid", result=AuditResult.FAILURE
    ).exists()


def test_webhook_accepts_valid_event_and_records_it():
    url = reverse("stripe-webhook")
    event = WebhookEvent(
        event_id="evt_100",
        event_type="checkout.session.completed",
        payload={"id": "evt_100"},
    )
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
        return_value=event,
    ):
        resp = APIClient().post(url, data=b"{}", content_type="application/json")
    assert resp.status_code == 200
    row = StripeEvent.objects.get(stripe_event_id="evt_100")
    assert row.processed_at is not None


def test_webhook_processing_failure_rolls_back_ledger_row():
    """If _process_event raises, the atomic block rolls back the freshly-created
    row so no partial state (processed_at=NULL) survives (Stripe will retry)."""
    from apps.billing.services.billing_service import BillingService

    event = WebhookEvent(event_id="evt_boom", event_type="checkout.session.completed", payload={})
    with (
        patch(
            "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
            return_value=event,
        ),
        patch.object(BillingService, "_process_event", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError),
    ):
        BillingService().record_webhook_event(payload=b"{}", signature_header="t=1,v1=x")
    assert StripeEvent.objects.filter(stripe_event_id="evt_boom").count() == 0


def test_webhook_does_not_persist_pii_payload():
    """The full Stripe event body (with customer PII) must NOT be stored — only
    the non-PII envelope (event id + type)."""
    url = reverse("stripe-webhook")
    event = WebhookEvent(
        event_id="evt_pii",
        event_type="checkout.session.completed",
        payload={"data": {"object": {"customer_details": {"email": "leak@example.com"}}}},
    )
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
        return_value=event,
    ):
        APIClient().post(url, data=b"{}", content_type="application/json")
    row = StripeEvent.objects.get(stripe_event_id="evt_pii")
    assert row.payload == {}


def test_webhook_unhandled_event_type_stays_reprocessable():
    """Code-review fix (2026-08): an event type with no handler YET must NOT
    be permanently marked `processed_at` — Stripe never redelivers a 200'd
    event, so a future handler added for this type would otherwise never see
    the historical occurrences that already landed before it existed."""
    url = reverse("stripe-webhook")
    event = WebhookEvent(
        event_id="evt_unhandled",
        event_type="some.future.event.type",
        payload={"id": "evt_unhandled"},
    )
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
        return_value=event,
    ):
        resp = APIClient().post(url, data=b"{}", content_type="application/json")
    assert resp.status_code == 200
    row = StripeEvent.objects.get(stripe_event_id="evt_unhandled")
    assert row.processed_at is None
    assert row.event_type == "some.future.event.type"


def test_webhook_is_idempotent_on_redelivery():
    url = reverse("stripe-webhook")
    event = WebhookEvent(
        event_id="evt_dup",
        event_type="checkout.session.completed",
        payload={"id": "evt_dup"},
    )
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.handle_webhook",
        return_value=event,
    ):
        first = APIClient().post(url, data=b"{}", content_type="application/json")
        second = APIClient().post(url, data=b"{}", content_type="application/json")
    assert first.status_code == 200
    assert second.status_code == 200
    assert StripeEvent.objects.filter(stripe_event_id="evt_dup").count() == 1
