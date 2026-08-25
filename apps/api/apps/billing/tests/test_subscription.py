"""Subscription tier + gating tests — Story 5.2."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.billing.models import Subscription
from apps.billing.services.subscription_service import SubscriptionService
from apps.core.exceptions import InsufficientPlan
from apps.core.rls import bypass_rls

pytestmark = pytest.mark.django_db


def _make_user(email: str = "sub@test.local") -> User:
    with bypass_rls(reason="test_setup.subscription"):
        return User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )


def _sub(user, **kwargs) -> Subscription:
    with bypass_rls(reason="test_setup.subscription"):
        return Subscription.objects.create(user=user, **kwargs)


# --- AC2 is_premium / grace math -------------------------------------------


def test_is_active_now_active_premium():
    u = _make_user()
    sub = _sub(u, tier="premium", status="active")
    assert sub.is_active_now is True
    assert u.is_premium is True


def test_is_active_now_free():
    u = _make_user()
    _sub(u, tier="free", status="active")
    assert u.is_premium is False


def test_past_due_within_grace_is_premium():
    u = _make_user()
    _sub(u, tier="premium", status="past_due", grace_until=timezone.now() + timedelta(days=2))
    assert u.is_premium is True


def test_past_due_grace_expired_not_premium():
    u = _make_user()
    _sub(u, tier="premium", status="past_due", grace_until=timezone.now() - timedelta(hours=1))
    assert u.is_premium is False


def test_no_subscription_not_premium():
    u = _make_user()
    assert u.is_premium is False


# --- AC3 gating ------------------------------------------------------------


def test_require_premium_raises_for_free():
    u = _make_user()
    with pytest.raises(InsufficientPlan):
        SubscriptionService.require_premium(u)


def test_require_premium_ok_for_premium():
    u = _make_user()
    _sub(u, tier="premium", status="active")
    SubscriptionService.require_premium(u)  # no raise


# --- AC4 webhook lifecycle -------------------------------------------------


def test_checkout_completed_activates_premium():
    u = _make_user()
    SubscriptionService.apply_event(
        event_type="checkout.session.completed",
        obj={"client_reference_id": u.id, "customer": "cus_1", "subscription": "sub_1"},
    )
    sub = Subscription.objects.get(user=u)
    assert sub.tier == "premium" and sub.status == "active"
    assert sub.stripe_subscription_id == "sub_1"


def test_subscription_deleted_cancels():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_x")
    SubscriptionService.apply_event(event_type="customer.subscription.deleted", obj={"id": "sub_x"})
    sub = Subscription.objects.get(user=u)
    assert sub.status == "cancelled" and sub.tier == "free"


def test_payment_failed_sets_past_due_with_grace():
    u = _make_user()
    _sub(u, tier="premium", status="active", stripe_subscription_id="sub_y")
    SubscriptionService.apply_event(
        event_type="invoice.payment_failed", obj={"subscription": "sub_y"}
    )
    sub = Subscription.objects.get(user=u)
    assert sub.status == "past_due"
    assert sub.grace_until is not None and sub.grace_until > timezone.now()


def test_subscription_updated_recovers_to_active():
    u = _make_user()
    _sub(
        u,
        tier="premium",
        status="past_due",
        grace_until=timezone.now() + timedelta(days=1),
        stripe_subscription_id="sub_z",
    )
    SubscriptionService.apply_event(
        event_type="customer.subscription.updated", obj={"id": "sub_z", "status": "active"}
    )
    sub = Subscription.objects.get(user=u)
    assert sub.status == "active" and sub.grace_until is None


# --- AC5 dunning -----------------------------------------------------------


def test_dunning_downgrades_grace_expired():
    u = _make_user()
    _sub(u, tier="premium", status="past_due", grace_until=timezone.now() - timedelta(hours=1))
    with patch("apps.billing.services.subscription_service._send_dunning_email"):
        downgraded = SubscriptionService.process_dunning()
    assert downgraded == 1
    sub = Subscription.objects.get(user=u)
    assert sub.tier == "free" and sub.status == "cancelled"


def test_dunning_keeps_in_grace():
    u = _make_user()
    _sub(u, tier="premium", status="past_due", grace_until=timezone.now() + timedelta(days=2))
    with patch("apps.billing.services.subscription_service._send_dunning_email"):
        downgraded = SubscriptionService.process_dunning()
    assert downgraded == 0
    assert Subscription.objects.get(user=u).tier == "premium"


# --- AC6 status endpoint + serializer --------------------------------------


def test_subscription_status_endpoint():
    u = _make_user()
    _sub(u, tier="premium", status="active")
    client = APIClient()
    client.force_authenticate(user=u)
    resp = client.get(reverse("billing:subscription"))
    assert resp.status_code == 200
    assert resp.data["tier"] == "premium"
    assert resp.data["is_premium"] is True


def test_subscription_status_requires_auth():
    resp = APIClient().get(reverse("billing:subscription"))
    assert resp.status_code in (401, 403)
