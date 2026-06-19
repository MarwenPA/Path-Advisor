"""Integration tests for GET /api/v1/students/me/profile/maturity — Story 2.7 AC9."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.students.models import BulletinsStatus, OnboardingStep1Status, OnboardingStep2Status, StudentLevelProfile, StudentProfile

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="sarah@test.local",
        password="Strong1!pass",
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def client_authed(student):
    c = APIClient()
    c.force_authenticate(user=student)
    return c


MATURITY_URL = reverse("students:me-profile-maturity")


@pytest.mark.django_db
class TestProfileMaturityEndpoint:
    def test_no_profile_returns_base(self, client_authed):
        resp = client_authed.get(MATURITY_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "base"
        assert isinstance(data["next_actions"], list)
        assert "computed_at" in data

    def test_base_level_has_expected_next_actions(self, client_authed, student):
        StudentProfile.objects.create(
            user=student,
            onboarding_step1_status=OnboardingStep1Status.SKIPPED,
            bulletins_status=BulletinsStatus.PENDING,
        )
        resp = client_authed.get(MATURITY_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "base"
        icons = [a["icon"] for a in data["next_actions"]]
        assert "bulletins" in icons

    def test_partial_bulletins_returns_enriched(self, client_authed, student):
        profile = StudentProfile.objects.create(
            user=student,
            onboarding_step1_status=OnboardingStep1Status.COMPLETED,
            passions=["sport", "musique", "arts", "cinema", "nature"],
            bulletins_status=BulletinsStatus.PARTIAL,
        )
        StudentLevelProfile.objects.create(
            profile=profile,
            onboarding_step2_status=OnboardingStep2Status.COMPLETED,
        )
        resp = client_authed.get(MATURITY_URL)
        assert resp.status_code == 200
        assert resp.json()["level"] == "enriched"

    def test_all_completed_returns_complete(self, client_authed, student):
        profile = StudentProfile.objects.create(
            user=student,
            onboarding_step1_status=OnboardingStep1Status.COMPLETED,
            passions=["sport", "musique", "arts"],
            bulletins_status=BulletinsStatus.COMPLETED,
        )
        StudentLevelProfile.objects.create(
            profile=profile,
            onboarding_step2_status=OnboardingStep2Status.COMPLETED,
        )
        resp = client_authed.get(MATURITY_URL)
        assert resp.status_code == 200
        assert resp.json()["level"] == "complete"

    def test_complete_has_no_next_actions(self, client_authed, student):
        profile = StudentProfile.objects.create(
            user=student,
            onboarding_step1_status=OnboardingStep1Status.COMPLETED,
            passions=["sport", "musique", "arts"],
            bulletins_status=BulletinsStatus.COMPLETED,
        )
        StudentLevelProfile.objects.create(
            profile=profile,
            onboarding_step2_status=OnboardingStep2Status.COMPLETED,
        )
        resp = client_authed.get(MATURITY_URL)
        assert resp.json()["next_actions"] == []

    def test_unauthenticated_returns_401(self):
        c = APIClient()
        resp = c.get(MATURITY_URL)
        assert resp.status_code in (401, 403)
