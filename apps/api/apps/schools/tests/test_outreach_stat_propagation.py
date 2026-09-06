"""Story 5.8 — early-outreach response → AdmissionStat propagation.

Covers:
- `AdmissionPredictionService.apply_outreach_response_delta` (service level)
- `AdmissionStatView` skipping its usual recompute within the 24h window
  a response just nudged the stat (the guard-rail this story adds)
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.schools.models import AdmissionStat, School
from apps.schools.services import AdmissionPredictionService

pytestmark = pytest.mark.django_db


def _create_user_bypassing_rls(**kwargs) -> User:
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', 'true', true)")
    user = User.objects.create_user(**kwargs)
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', '', true)")
    return user


@pytest.fixture
def student_user() -> User:
    return _create_user_bypassing_rls(
        email="eleve-stat-propagation@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def student_client(student_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def school(db) -> School:
    return School.objects.create(
        slug="ecole-stat-propagation-test",
        name="École Stat Propagation Test",
        type=School.Type.ECOLE_INGENIEUR,
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
        postal_code="69000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
    )


class TestApplyOutreachResponseDelta:
    def test_interested_adds_15_points(self, student_user, school):
        service = AdmissionPredictionService()
        service.upsert_stat(school=school, user=student_user, average_grade=12, has_bulletins=True)
        before = AdmissionStat.objects.get(school=school, user=student_user).expected_proba

        stat = service.apply_outreach_response_delta(
            school=school, user=student_user, action="interested"
        )

        assert stat.expected_proba == min(95, before + 15)
        assert stat.previous_proba == before
        assert stat.outreach_delta_applied_at is not None

    def test_not_aligned_subtracts_15_points(self, student_user, school):
        service = AdmissionPredictionService()
        service.upsert_stat(school=school, user=student_user, average_grade=12, has_bulletins=True)
        before = AdmissionStat.objects.get(school=school, user=student_user).expected_proba

        stat = service.apply_outreach_response_delta(
            school=school, user=student_user, action="not_aligned"
        )

        assert stat.expected_proba == max(5, before - 15)

    def test_never_drops_below_the_anti_humiliation_floor(self, student_user, school):
        service = AdmissionPredictionService()
        AdmissionStat.objects.create(
            school=school,
            user=student_user,
            min_proba=5,
            expected_proba=10,
            max_proba=30,
            label=AdmissionStat.Label.AUDACIEUX,
            context_line="x",
        )

        stat = service.apply_outreach_response_delta(
            school=school, user=student_user, action="not_aligned"
        )

        assert stat.expected_proba == 5

    def test_creates_a_baseline_if_none_exists_yet(self, student_user, school):
        assert not AdmissionStat.objects.filter(school=school, user=student_user).exists()
        service = AdmissionPredictionService()

        stat = service.apply_outreach_response_delta(
            school=school, user=student_user, action="interview_requested"
        )

        assert stat.pk is not None
        assert stat.outreach_delta_applied_at is not None


class TestAdmissionStatViewSkipsRecomputeAfterOutreachDelta:
    def test_recent_outreach_delta_is_not_overwritten_by_a_fresh_get(
        self, student_client, student_user, school
    ):
        service = AdmissionPredictionService()
        service.upsert_stat(school=school, user=student_user, average_grade=8, has_bulletins=True)
        nudged = service.apply_outreach_response_delta(
            school=school, user=student_user, action="interested"
        )

        response = student_client.get(
            reverse("schools:school-admission-stat", kwargs={"slug": school.slug})
        )

        assert response.status_code == 200
        assert response.json()["expected_proba"] == nudged.expected_proba
        assert response.json()["previous_proba"] == nudged.previous_proba

    def test_recompute_resumes_once_the_24h_window_has_passed(
        self, student_client, student_user, school
    ):
        service = AdmissionPredictionService()
        service.upsert_stat(school=school, user=student_user, average_grade=8, has_bulletins=True)
        service.apply_outreach_response_delta(school=school, user=student_user, action="interested")
        AdmissionStat.objects.filter(school=school, user=student_user).update(
            outreach_delta_applied_at=timezone.now() - timedelta(hours=25)
        )

        response = student_client.get(
            reverse("schools:school-admission-stat", kwargs={"slug": school.slug})
        )

        assert response.status_code == 200
        # Recompute ran again — expected_proba is back to the bulletin-based
        # prediction, not the (now stale) outreach-nudged value.
        stat = AdmissionStat.objects.get(school=school, user=student_user)
        assert response.json()["expected_proba"] == stat.expected_proba
