"""Parent-pays-premium-for-child tests — Story 6.4.

Covers:
- POST /api/v1/family/children/{id}/checkout-session/ — AC1/AC2
- GET  /api/v1/family/children/{id}/subscription/      — AC3
- POST /api/v1/family/children/{id}/subscription/cancel/ — AC3
- webhook: checkout.session.completed with paid_by metadata — AC4
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.billing.models import Subscription
from apps.billing.services.provider import CheckoutSession
from apps.billing.services.subscription_service import SubscriptionService
from apps.core.rls import bypass_rls
from apps.family.models import ParentStudentLink

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_parent_billing_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


def _linked_pair():
    parent = _uf(email="parent-billing@test.local", role=UserRole.PARENT)
    student = _uf(email="student-billing@test.local", role=UserRole.STUDENT)
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=student)
    return parent, student


class TestParentChildCheckoutSession:
    def test_creates_a_checkout_session_with_child_as_beneficiary(self):
        parent, student = _linked_pair()
        client = APIClient()
        client.force_authenticate(user=parent)

        with patch(
            "apps.billing.services.stripe_provider.StripeProvider.create_checkout_session",
            return_value=CheckoutSession(
                session_id="cs_1", checkout_url="https://stripe.test/cs_1"
            ),
        ) as mock_create:
            response = client.post(
                reverse("family:parent-child-checkout-session", kwargs={"student_id": student.id})
            )

        assert response.status_code == 201, response.content
        assert response.json()["checkout_url"] == "https://stripe.test/cs_1"
        _, kwargs = mock_create.call_args
        assert kwargs["client_reference_id"] == student.id
        assert kwargs["customer_email"] == parent.email
        assert kwargs["metadata"] == {"paid_by_user_id": parent.id}

    def test_unlinked_parent_gets_403(self):
        parent = _uf(email="parent-unlinked@test.local", role=UserRole.PARENT)
        student = _uf(email="student-unlinked@test.local", role=UserRole.STUDENT)
        client = APIClient()
        client.force_authenticate(user=parent)

        response = client.post(
            reverse("family:parent-child-checkout-session", kwargs={"student_id": student.id})
        )

        assert response.status_code == 403

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.post(
            reverse("family:parent-child-checkout-session", kwargs={"student_id": "usr_x"})
        )
        assert response.status_code == 401


class TestParentChildSubscriptionStatus:
    def test_reflects_the_childs_tier(self):
        parent, student = _linked_pair()
        with bypass_rls(reason="test_setup.create_subscription"):
            Subscription.objects.create(
                user=student, tier="premium", status="active", paid_by=parent
            )
        client = APIClient()
        client.force_authenticate(user=parent)

        response = client.get(
            reverse("family:parent-child-subscription-status", kwargs={"student_id": student.id})
        )

        assert response.status_code == 200, response.content
        body = response.json()
        assert body["tier"] == "premium"
        assert body["is_premium"] is True
        assert body["paid_by_parent"] is True

    def test_free_child_with_no_subscription_row(self):
        parent, student = _linked_pair()
        client = APIClient()
        client.force_authenticate(user=parent)

        response = client.get(
            reverse("family:parent-child-subscription-status", kwargs={"student_id": student.id})
        )

        assert response.status_code == 200
        assert response.json()["tier"] == "free"
        assert response.json()["paid_by_parent"] is False


class TestParentChildCancelSubscription:
    def test_schedules_cancellation_at_period_end(self):
        parent, student = _linked_pair()
        with bypass_rls(reason="test_setup.create_subscription"):
            Subscription.objects.create(
                user=student,
                tier="premium",
                status="active",
                stripe_subscription_id="sub_123",
                paid_by=parent,
            )
        client = APIClient()
        client.force_authenticate(user=parent)

        with patch("apps.billing.services.stripe_provider.StripeProvider.schedule_cancellation"):
            response = client.post(
                reverse(
                    "family:parent-child-subscription-cancel", kwargs={"student_id": student.id}
                )
            )

        assert response.status_code == 200, response.content
        assert response.json()["cancel_at_period_end"] is True
        # Still premium — only takes effect at period end.
        assert response.json()["is_premium"] is True

    def test_unlinked_parent_cannot_cancel_another_students_subscription(self):
        parent = _uf(email="parent-nolink@test.local", role=UserRole.PARENT)
        student = _uf(email="student-nolink@test.local", role=UserRole.STUDENT)
        with bypass_rls(reason="test_setup.create_subscription"):
            Subscription.objects.create(
                user=student, tier="premium", status="active", stripe_subscription_id="sub_456"
            )
        client = APIClient()
        client.force_authenticate(user=parent)

        response = client.post(
            reverse("family:parent-child-subscription-cancel", kwargs={"student_id": student.id})
        )

        assert response.status_code == 403


class TestWebhookParentPaidMetadata:
    def test_checkout_completed_with_paid_by_metadata_sets_paid_by_and_audits(self):
        parent, student = _linked_pair()

        applied = SubscriptionService.apply_event(
            event_type="checkout.session.completed",
            obj={
                "client_reference_id": student.id,
                "customer": "cus_1",
                "subscription": "sub_1",
                "metadata": {"paid_by_user_id": parent.id},
            },
        )

        assert applied is True
        with bypass_rls(reason="test_assert.read_subscription"):
            sub = Subscription.objects.get(user=student)
        assert sub.paid_by_id == parent.id
        assert sub.tier == "premium"
        with bypass_rls(reason="test_assert.read_audit"):
            assert AuditLog.objects.filter(
                action="billing.premium_purchased_by_parent", subject_id=student.id
            ).exists()

    def test_checkout_completed_without_metadata_leaves_paid_by_null(self):
        student = _uf(email="self-pay-student@test.local", role=UserRole.STUDENT)

        SubscriptionService.apply_event(
            event_type="checkout.session.completed",
            obj={"client_reference_id": student.id, "customer": "cus_2", "subscription": "sub_2"},
        )

        with bypass_rls(reason="test_assert.read_subscription"):
            sub = Subscription.objects.get(user=student)
        assert sub.paid_by_id is None
