"""Cohort dashboard tests — Story 6.6.

Covers:
- GET /api/v1/establishments/cohort-dashboard/ — AC (KPIs, top métiers,
  distribution filière, activité récente)
- Only the counselor's own establishment's students are aggregated
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.establishments.models import (
    Cohort,
    EstablishmentType,
    LicenseType,
    StudentImportInvitation,
    StudentImportInvitationStatus,
)
from apps.establishments.models import Establishment as EstablishmentModel
from apps.students.models import OnboardingStep1Status, StudentProfile

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mock_ai_recommendations():
    with patch("apps.family.services.parent_view.compute_recommendations") as mock_reco:
        mock_reco.return_value = {
            "results": [
                {
                    "id": "prof_1",
                    "slug": "infirmier",
                    "name": "Infirmier·ère",
                    "sector": "santé",
                    "score": 80,
                    "confidence_level": "high",
                    "signals_contributifs": [],
                    "phrase_recopiable": "",
                }
            ]
        }
        yield mock_reco


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_dashboard_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


_uai_counter = iter(range(3000, 4000))


def _establishment() -> EstablishmentModel:
    n = next(_uai_counter)
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentModel.objects.create(
            name=f"Lycée Dashboard Test {n}",
            type=EstablishmentType.LYCEE,
            city="Paris",
            uai=f"075{n:04d}A",
            contact_name="Karim",
            contact_email=f"karim{n}@ex.test",
            license_start="2026-09-01",
            license_end="2027-08-31",
            license_type=LicenseType.PILOTE_GRATUIT,
        )


def _cohort(establishment) -> Cohort:
    with bypass_rls(reason="test_setup.create_cohort"):
        return Cohort.objects.create(
            establishment=establishment,
            name="Terminale 2025-2026",
            school_year="2025-2026",
            tenant_id=establishment.id,
            user_id="usr_test_setup",
        )


def _accepted_student(*, cohort, completed: bool) -> User:
    student = _uf(email=f"student-dash-{cohort.id}-{completed}@test.local", role=UserRole.STUDENT)
    with bypass_rls(reason="test_setup.create_invitation_and_profile"):
        StudentImportInvitation.objects.create(
            cohort=cohort,
            user=student,
            token="tok_" + student.id,
            status=StudentImportInvitationStatus.ACCEPTED,
            accepted_at=timezone.now(),
        )
        StudentProfile.objects.create(
            user=student,
            onboarding_step1_status=(
                OnboardingStep1Status.COMPLETED if completed else OnboardingStep1Status.PENDING
            ),
        )
    return student


def _counselor(establishment) -> User:
    counselor = _uf(
        email="counselor-dashboard@test.local",
        role=UserRole.COUNSELOR,
        tenant_id=establishment.id,
    )
    counselor.is_verified = lambda: True
    return counselor


class TestCohortDashboard:
    def test_dashboard_returns_kpis_and_sections(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        _accepted_student(cohort=cohort, completed=True)
        _accepted_student(cohort=cohort, completed=False)
        counselor = _counselor(establishment)
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(reverse("establishments_cohort:counselor-cohort-dashboard"))

        assert response.status_code == 200, response.content
        body = response.json()
        assert body["kpis"]["nb_eleves"] == 2
        assert body["kpis"]["taux_completion_profil"] == 50.0
        assert body["kpis"]["nb_eleves_mode_degrade"] == 1
        assert body["top_metiers"] == [{"name": "Infirmier·ère", "count": 2}]
        assert len(body["eleves"]) == 2

    def test_dashboard_excludes_students_from_other_establishments(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        _accepted_student(cohort=cohort, completed=True)

        other_establishment = _establishment()
        other_cohort = _cohort(other_establishment)
        _accepted_student(cohort=other_cohort, completed=True)

        counselor = _counselor(establishment)
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(reverse("establishments_cohort:counselor-cohort-dashboard"))

        assert response.status_code == 200
        assert response.json()["kpis"]["nb_eleves"] == 1

    def test_dashboard_requires_counselor_role(self):
        student = _uf(email="intruder-dashboard@test.local", role=UserRole.STUDENT)
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.get(reverse("establishments_cohort:counselor-cohort-dashboard"))

        assert response.status_code == 403
