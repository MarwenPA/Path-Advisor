"""Tests for Story 2.6 — GET /me/profile + history endpoints."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserStatus
from apps.students.models import StudentProfile


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="sarah@test.local",
        password="Strong1!pass",  # noqa: S106
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def profile(user):
    return StudentProfile.objects.create(
        user=user,
        onboarding_step1_status="completed",
        passions=["sciences", "cinema"],
        valeurs=["autonomie", "curiosite"],
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestGetProfileAggregated:
    def test_returns_200(self, auth_client, profile):
        response = auth_client.get(reverse("students:me-profile"))
        assert response.status_code == 200

    def test_response_contains_passions(self, auth_client, profile):
        response = auth_client.get(reverse("students:me-profile"))
        data = response.json()
        assert "passions" in data
        assert data["passions"] == ["sciences", "cinema"]

    def test_response_contains_bulletins_status(self, auth_client, profile):
        response = auth_client.get(reverse("students:me-profile"))
        data = response.json()
        assert "bulletins_status" in data

    def test_response_contains_updated_at(self, auth_client, profile):
        response = auth_client.get(reverse("students:me-profile"))
        data = response.json()
        assert "updated_at" in data

    def test_unauthenticated_returns_401(self, profile):
        response = APIClient().get(reverse("students:me-profile"))
        assert response.status_code == 401


class TestProfileRecompute:
    def test_post_recompute_returns_202(self, auth_client, profile):
        response = auth_client.post(reverse("students:me-profile-recompute"))
        assert response.status_code == 202

    def test_unauthenticated_returns_401(self, profile):
        response = APIClient().post(reverse("students:me-profile-recompute"))
        assert response.status_code == 401


class TestProfileHistory:
    def test_get_history_returns_200(self, auth_client, profile):
        response = auth_client.get(reverse("students:me-profile-history"))
        assert response.status_code == 200

    def test_empty_history_returns_empty_list(self, auth_client, profile):
        response = auth_client.get(reverse("students:me-profile-history"))
        data = response.json()
        assert data["results"] == []

    def test_unauthenticated_returns_401(self, profile):
        response = APIClient().get(reverse("students:me-profile-history"))
        assert response.status_code == 401


class TestProfileHistorySnapshot:
    def test_major_change_creates_history_entry(self, auth_client, profile):
        """PATCH with motive=profile_major_change should snapshot the profile."""
        response = auth_client.post(
            reverse("students:me-profile-history-snapshot"),
            {
                "archived_reason": "major_change_filiere",
                "previous_state": {
                    "level": "lycee_terminale",
                    "filiere": "general",
                    "specialites": ["mathematiques", "svt"],
                },
            },
            format="json",
        )
        assert response.status_code == 201

    def test_history_entry_appears_in_list(self, auth_client, profile):
        auth_client.post(
            reverse("students:me-profile-history-snapshot"),
            {
                "archived_reason": "major_change_filiere",
                "previous_state": {"level": "lycee_terminale"},
            },
            format="json",
        )
        response = auth_client.get(reverse("students:me-profile-history"))
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["archived_reason"] == "major_change_filiere"

    def test_cross_tenant_history_not_visible(self, profile):
        other_user = User.objects.create_user(
            email="other@test.local",
            password="Strong1!pass",  # noqa: S106
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        other_profile = StudentProfile.objects.create(user=other_user)
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)

        # Sarah creates a snapshot
        from apps.students.models import StudentProfileHistory
        StudentProfileHistory.objects.create(
            student=profile,
            archived_reason="major_change_filiere",
            previous_state={"level": "lycee_terminale"},
        )

        # Other user's history must be empty
        response = other_client.get(reverse("students:me-profile-history"))
        data = response.json()
        assert len(data["results"]) == 0
