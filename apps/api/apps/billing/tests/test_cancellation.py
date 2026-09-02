"""Story 5.3 — cancellation-at-period-end + confirmation email tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.billing.exceptions import NoActiveSubscription
from apps.billing.models import Subscription
from apps.billing.services.subscription_service import SubscriptionService
from apps.core.rls import bypass_rls

pytestmark = [pytest.mark.django_db, pytest.mark.postgresql_only]


def _make_user() -> User:
    with bypass_rls(reason="test_setup.cancellation"):
        return User.objects.create_user(
            email="cancel@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )


def _sub(user, **kwargs) -> Subscription:
    with bypass_rls(reason="test_setup.cancellation"):
        return Subscription.objects.create(user=user, **kwargs)


# --- AC3 service layer ------------------------------------------------------


def test_request_cancellation_schedules_at_period_end():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_1")
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.schedule_cancellation"
    ) as mock_schedule:
        sub = SubscriptionService.request_cancellation(user=u)
    mock_schedule.assert_called_once_with(stripe_subscription_id="sub_1")
    assert sub.cancel_at_period_end is True
    # Premium stays live — this is a schedule, not an immediate downgrade.
    assert sub.is_active_now is True


def test_request_cancellation_is_idempotent():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_1")
    with patch(
        "apps.billing.services.stripe_provider.StripeProvider.schedule_cancellation"
    ) as mock_schedule:
        SubscriptionService.request_cancellation(user=u)
        SubscriptionService.request_cancellation(user=u)
    mock_schedule.assert_called_once()


def test_request_cancellation_never_calls_immediate_cancel():
    """Distinct provider method — must not reuse the immediate `cancel_subscription`
    used by merge-on-second-checkout / RGPD pre_delete."""
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_1")
    with (
        patch("apps.billing.services.stripe_provider.StripeProvider.schedule_cancellation"),
        patch(
            "apps.billing.services.stripe_provider.StripeProvider.cancel_subscription"
        ) as mock_immediate,
    ):
        SubscriptionService.request_cancellation(user=u)
    mock_immediate.assert_not_called()


def test_request_cancellation_raises_for_free_user():
    u = _make_user()
    with pytest.raises(NoActiveSubscription):
        SubscriptionService.request_cancellation(user=u)


def test_request_cancellation_raises_without_stripe_subscription_id():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="")
    with pytest.raises(NoActiveSubscription):
        SubscriptionService.request_cancellation(user=u)


# --- AC3 webhook sync of cancel_at_period_end -------------------------------


def test_subscription_updated_syncs_cancel_at_period_end_true():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_1")
    SubscriptionService.apply_event(
        event_type="customer.subscription.updated",
        obj={"id": "sub_1", "status": "active", "cancel_at_period_end": True},
    )
    assert Subscription.objects.get(user=u).cancel_at_period_end is True


def test_subscription_deleted_clears_cancel_at_period_end():
    u = _make_user()
    _sub(
        u,
        tier="premium",
        status="active",
        stripe_subscription_id="sub_1",
        cancel_at_period_end=True,
    )
    SubscriptionService.apply_event(event_type="customer.subscription.deleted", obj={"id": "sub_1"})
    sub = Subscription.objects.get(user=u)
    assert sub.tier == "free" and sub.cancel_at_period_end is False


def test_new_checkout_clears_prior_cancel_at_period_end():
    """A fresh activation is a new subscription, not a continuation of one the
    user had scheduled to end."""
    u = _make_user()
    _sub(
        u,
        tier="premium",
        status="active",
        stripe_subscription_id="sub_old",
        cancel_at_period_end=True,
    )
    SubscriptionService.apply_event(
        event_type="checkout.session.completed",
        obj={"client_reference_id": u.id, "customer": "cus_1", "subscription": "sub_new"},
    )
    assert Subscription.objects.get(user=u).cancel_at_period_end is False


# --- AC2 confirmation email --------------------------------------------------


def test_checkout_completed_sends_confirmation_email():
    u = _make_user()
    SubscriptionService.apply_event(
        event_type="checkout.session.completed",
        obj={"client_reference_id": u.id, "customer": "cus_1", "subscription": "sub_1"},
    )
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [u.email]


def test_checkout_completed_email_failure_does_not_block_activation():
    u = _make_user()
    with patch(
        "apps.billing.services.emails.send_premium_activated", side_effect=RuntimeError("smtp down")
    ):
        handled = SubscriptionService.apply_event(
            event_type="checkout.session.completed",
            obj={"client_reference_id": u.id, "customer": "cus_1", "subscription": "sub_1"},
        )
    assert handled is True
    assert Subscription.objects.get(user=u).tier == "premium"


# --- API endpoint ------------------------------------------------------------


def test_cancel_endpoint_requires_auth():
    resp = APIClient().post(reverse("billing:subscription-cancel"))
    assert resp.status_code in (401, 403)


def test_cancel_endpoint_404_when_no_subscription():
    u = _make_user()
    client = APIClient()
    client.force_authenticate(user=u)
    resp = client.post(reverse("billing:subscription-cancel"))
    assert resp.status_code == 404
    assert resp.data["type"].endswith("/no-active-subscription")


def test_cancel_endpoint_schedules_and_returns_status():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_1")
    client = APIClient()
    client.force_authenticate(user=u)
    with patch("apps.billing.services.stripe_provider.StripeProvider.schedule_cancellation"):
        resp = client.post(reverse("billing:subscription-cancel"))
    assert resp.status_code == 200
    assert resp.data["cancel_at_period_end"] is True
    assert resp.data["is_premium"] is True


def test_subscription_status_endpoint_includes_cancel_at_period_end():
    u = _make_user()
    _sub(u, tier="premium", status="active", cancel_at_period_end=True)
    client = APIClient()
    client.force_authenticate(user=u)
    resp = client.get(reverse("billing:subscription"))
    assert resp.status_code == 200
    assert resp.data["cancel_at_period_end"] is True
