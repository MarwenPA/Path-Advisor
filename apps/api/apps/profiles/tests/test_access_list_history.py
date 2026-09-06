"""Access history endpoint tests — Story 6.11.

Covers:
- GET /api/v1/profile/access-list/{id}/history/ — 90-day timestamped log
- GET /api/v1/profile/access-list/{id}/history.csv/ — CSV export
- `last_accessed_at` surfaced on the access-list entry itself
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from allauth.account.models import EmailAddress
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import ParentalConsent, ParentalConsentDecision, UserRole
from apps.accounts.tests.factories import UserFactory
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.rls import bypass_rls
from apps.establishments.models import (
    Cohort,
    CounselorConsent,
    CounselorConsentStatus,
    EstablishmentType,
    LicenseType,
)
from apps.establishments.models import Establishment as EstablishmentModel

pytestmark = pytest.mark.django_db


def _make_student(email: str = "student-history@example.test"):
    with bypass_rls(reason="test_setup.create_history_student"):
        user = UserFactory(email=email, role=UserRole.STUDENT)
        EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


_uai_counter = iter(range(5000, 6000))


def _establishment() -> EstablishmentModel:
    n = next(_uai_counter)
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentModel.objects.create(
            name=f"Lycée History Test {n}",
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
            name="Terminale History",
            school_year="2025-2026",
            tenant_id=establishment.id,
            user_id="usr_test_setup",
        )


def _counselor(establishment):
    with bypass_rls(reason="test_setup.create_history_counselor"):
        counselor = UserFactory(
            email="counselor-history@example.test",
            role=UserRole.COUNSELOR,
            tenant_id=establishment.id,
        )
    counselor.is_verified = lambda: True
    return counselor


class TestCounselorAccessHistory:
    def test_history_returns_consultations_within_90_days(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        student = _make_student()
        counselor = _counselor(establishment)
        with bypass_rls(reason="test_setup.create_granted_consent"):
            consent = CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
            )
        record_audit(
            action="establishments.counselor_profile_viewed",
            result=AuditResult.SUCCESS,
            actor=counselor,
            subject_id=student.id,
            metadata={"consent_id": consent.id},
        )

        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(student, backend="apps.accounts.backends.TenantAwareModelBackend")
        response = client.get(
            f"/api/v1/profile/access-list/counselor_consent:{consent.id}/history/"
        )

        assert response.status_code == 200, response.content
        assert len(response.json()["results"]) == 1

    def test_history_excludes_consultations_older_than_90_days(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        student = _make_student()
        counselor = _counselor(establishment)
        with bypass_rls(reason="test_setup.create_granted_consent"):
            consent = CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
            )
        with bypass_rls(reason="test_setup.old_audit_row"):
            from apps.audit.models import AuditLog

            AuditLog.objects.create(
                action="establishments.counselor_profile_viewed",
                result=AuditResult.SUCCESS,
                actor_id=counselor.id,
                actor_role=counselor.role,
                subject_id=student.id,
                metadata={},
                created_at=timezone.now() - timedelta(days=120),
            )

        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(student, backend="apps.accounts.backends.TenantAwareModelBackend")
        response = client.get(
            f"/api/v1/profile/access-list/counselor_consent:{consent.id}/history/"
        )

        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_history_csv_export(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        student = _make_student()
        counselor = _counselor(establishment)
        with bypass_rls(reason="test_setup.create_granted_consent"):
            consent = CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
            )
        record_audit(
            action="establishments.counselor_profile_viewed",
            result=AuditResult.SUCCESS,
            actor=counselor,
            subject_id=student.id,
            metadata={},
        )

        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(student, backend="apps.accounts.backends.TenantAwareModelBackend")
        response = client.get(
            f"/api/v1/profile/access-list/counselor_consent:{consent.id}/history.csv/"
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert "Date de consultation" in response.content.decode("utf-8")

    def test_history_requires_ownership(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        student = _make_student()
        intruder = _make_student(email="intruder-history@example.test")
        counselor = _counselor(establishment)
        with bypass_rls(reason="test_setup.create_granted_consent"):
            consent = CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
            )

        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(intruder, backend="apps.accounts.backends.TenantAwareModelBackend")
        response = client.get(
            f"/api/v1/profile/access-list/counselor_consent:{consent.id}/history/"
        )

        assert response.status_code == 200
        assert response.json()["results"] == []  # no consent row matches intruder+pk


class TestAccessListLastAccessedAt:
    def test_last_accessed_at_surfaced_for_counselor_entry(self):
        establishment = _establishment()
        cohort = _cohort(establishment)
        student = _make_student()
        counselor = _counselor(establishment)
        with bypass_rls(reason="test_setup.create_granted_consent"):
            CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
                last_accessed_at=timezone.now(),
            )

        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(student, backend="apps.accounts.backends.TenantAwareModelBackend")
        response = client.get("/api/v1/profile/access-list/")

        assert response.status_code == 200
        assert response.json()["results"][0]["last_accessed_at"] is not None

    def test_last_accessed_at_null_for_parental_entry(self):
        student = _make_student()
        with bypass_rls(reason="test_setup.create_parental_consent"):
            ParentalConsent.objects.create(
                student=student,
                parent_email="parent-history@example.test",
                token="tok_history_parent",
                decision=ParentalConsentDecision.GRANTED,
                decided_at=timezone.now(),
            )

        client = APIClient(REMOTE_ADDR="127.0.0.1")
        client.force_login(student, backend="apps.accounts.backends.TenantAwareModelBackend")
        response = client.get("/api/v1/profile/access-list/")

        assert response.status_code == 200
        assert response.json()["results"][0]["last_accessed_at"] is None
