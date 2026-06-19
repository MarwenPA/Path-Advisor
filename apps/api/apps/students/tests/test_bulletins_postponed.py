"""Tests for POST /api/v1/students/me/bulletins/postpone and .../banner/dismiss.

Story 2.5 — T1 + T7 backend.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from django.utils import timezone

from apps.accounts.models import User, UserStatus
from apps.students.models import BulletinsStatus, StudentProfile


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="lea@test.com",
        password="Strong1!pass",  # noqa: S106
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def profile(user):
    return StudentProfile.objects.create(user=user)


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ─────────────────────────────────────────────────────────────
# POST /api/v1/students/me/bulletins/postpone
# ─────────────────────────────────────────────────────────────


class TestPostponeEndpoint:
    def test_postpone_pending_sets_status_and_timestamp(self, auth_client, profile):
        response = auth_client.post(
            reverse("students:me-bulletins-postpone"), format="json"
        )
        assert response.status_code == 200
        profile.refresh_from_db()
        assert profile.bulletins_status == BulletinsStatus.POSTPONED
        assert profile.bulletins_postponed_at is not None

    def test_postpone_already_postponed_is_idempotent(self, auth_client, profile):
        auth_client.post(reverse("students:me-bulletins-postpone"), format="json")
        profile.refresh_from_db()
        first_ts = profile.bulletins_postponed_at

        response = auth_client.post(
            reverse("students:me-bulletins-postpone"), format="json"
        )
        assert response.status_code == 200
        profile.refresh_from_db()
        # Timestamp must NOT change on second call (idempotent)
        assert profile.bulletins_postponed_at == first_ts

    def test_postpone_when_completed_returns_409(self, auth_client, profile):
        profile.bulletins_status = BulletinsStatus.COMPLETED
        profile.save()

        response = auth_client.post(
            reverse("students:me-bulletins-postpone"), format="json"
        )
        assert response.status_code == 409

    def test_postpone_when_partial_returns_409(self, auth_client, profile):
        profile.bulletins_status = BulletinsStatus.PARTIAL
        profile.save()

        response = auth_client.post(
            reverse("students:me-bulletins-postpone"), format="json"
        )
        assert response.status_code == 409

    def test_postpone_unauthenticated_returns_401(self, profile):
        client = APIClient()
        response = client.post(
            reverse("students:me-bulletins-postpone"), format="json"
        )
        assert response.status_code == 401

    def test_postpone_response_shape(self, auth_client, profile):
        response = auth_client.post(
            reverse("students:me-bulletins-postpone"), format="json"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bulletins_status"] == "postponed"
        assert "bulletins_postponed_at" in data


# ─────────────────────────────────────────────────────────────
# POST /api/v1/students/me/bulletins/banner/dismiss
# ─────────────────────────────────────────────────────────────


class TestBannerDismissEndpoint:
    def test_dismiss_sets_ttl_seven_days(self, auth_client, profile):
        from django.utils import timezone

        before = timezone.now()
        response = auth_client.post(
            reverse("students:me-bulletins-banner-dismiss"), format="json"
        )
        after = timezone.now()

        assert response.status_code == 200
        profile.refresh_from_db()
        dismissed_until = profile.bulletins_postponed_banner_dismissed_until
        assert dismissed_until is not None
        # Must be now + 7 days (within the request window)
        from datetime import timedelta

        assert before + timedelta(days=7) <= dismissed_until <= after + timedelta(days=7)

    def test_dismiss_response_contains_dismissed_until(self, auth_client, profile):
        response = auth_client.post(
            reverse("students:me-bulletins-banner-dismiss"), format="json"
        )
        assert response.status_code == 200
        data = response.json()
        assert "bulletins_postponed_banner_dismissed_until" in data

    def test_dismiss_unauthenticated_returns_401(self, profile):
        client = APIClient()
        response = client.post(
            reverse("students:me-bulletins-banner-dismiss"), format="json"
        )
        assert response.status_code == 401

    def test_dismiss_idempotent_updates_ttl(self, auth_client, profile):
        """Second dismiss must refresh the 7-day window."""
        from django.utils import timezone

        auth_client.post(
            reverse("students:me-bulletins-banner-dismiss"), format="json"
        )
        profile.refresh_from_db()
        first_ts = profile.bulletins_postponed_banner_dismissed_until

        # Small sleep not needed — just call again; DRF timestamps are ≥ first
        response = auth_client.post(
            reverse("students:me-bulletins-banner-dismiss"), format="json"
        )
        assert response.status_code == 200
        profile.refresh_from_db()
        second_ts = profile.bulletins_postponed_banner_dismissed_until
        assert second_ts >= first_ts
