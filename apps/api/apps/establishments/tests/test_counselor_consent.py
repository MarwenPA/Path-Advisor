"""Counselor consent tests — Story 6.7.

Covers:
- POST /api/v1/establishments/students/{id}/consent-request/  — AC (request)
- GET  /api/v1/establishments/consent-requests/                — student's own
- POST /api/v1/establishments/consent-requests/{id}/decide/    — AC (decide)
- 7-day cooldown after a refusal
- CounselorConsentSource plugs into the unified access-list (Story 6.11 seam)
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.establishments.exceptions import ConsentCooldownActive
from apps.establishments.models import (
    Cohort,
    CounselorConsent,
    CounselorConsentStatus,
    EstablishmentType,
    LicenseType,
    StudentImportInvitation,
    StudentImportInvitationStatus,
)
from apps.establishments.models import Establishment as EstablishmentModel
from apps.establishments.services.counselor_consent import request_consent
from apps.profiles.access_list.aggregator import AccessListAggregator
from apps.profiles.access_list.sources.counselor_consent import CounselorConsentSource

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_consent_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


_uai_counter = iter(range(1, 1000))


def _establishment() -> EstablishmentModel:
    n = next(_uai_counter)
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentModel.objects.create(
            name=f"Lycée Consent Test {n}",
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


def _accepted_invitation(*, cohort, student) -> StudentImportInvitation:
    with bypass_rls(reason="test_setup.create_invitation"):
        return StudentImportInvitation.objects.create(
            cohort=cohort,
            user=student,
            token="tok_" + student.id,
            status=StudentImportInvitationStatus.ACCEPTED,
            accepted_at=timezone.now(),
        )


def _setup():
    establishment = _establishment()
    cohort = _cohort(establishment)
    counselor = _uf(
        email="counselor-consent@test.local", role=UserRole.COUNSELOR, tenant_id=establishment.id
    )
    # `IsCounselor.requires_mfa_verified=True` checks `user.is_verified()`,
    # a method django-otp's OTPMiddleware attaches after a real OTP
    # challenge — `force_authenticate` skips that middleware entirely. Same
    # monkeypatch pattern as `apps/outreach/tests/test_school_reception.py`.
    counselor.is_verified = lambda: True
    student = _uf(email="student-consent@test.local", role=UserRole.STUDENT)
    _accepted_invitation(cohort=cohort, student=student)
    return counselor, student, cohort


class TestCounselorConsentRequest:
    def test_counselor_can_request_consent(self):
        counselor, student, cohort = _setup()
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.post(
            reverse(
                "establishments_cohort:counselor-consent-request",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 201, response.content
        assert response.json()["status"] == "pending"
        with bypass_rls(reason="test_assert.read_consent"):
            consent = CounselorConsent.objects.get(student=student, counselor=counselor)
        assert consent.cohort_id == cohort.id

    def test_student_gets_403(self):
        _, student, _ = _setup()
        other_student = _uf(email="other-student-consent@test.local", role=UserRole.STUDENT)
        client = APIClient()
        client.force_authenticate(user=other_student)

        response = client.post(
            reverse(
                "establishments_cohort:counselor-consent-request",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 403

    def test_counselor_from_another_establishment_gets_403(self):
        _, student, _ = _setup()
        other_establishment = _establishment()
        other_counselor = _uf(
            email="counselor-other-est@test.local",
            role=UserRole.COUNSELOR,
            tenant_id=other_establishment.id,
        )
        other_counselor.is_verified = lambda: True
        client = APIClient()
        client.force_authenticate(user=other_counselor)

        response = client.post(
            reverse(
                "establishments_cohort:counselor-consent-request",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 403

    def test_cooldown_blocks_re_request_within_7_days(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_refused_consent"):
            CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.REFUSED,
                decided_at=timezone.now() - timedelta(days=2),
            )

        with pytest.raises(ConsentCooldownActive):
            request_consent(counselor=counselor, student=student, cohort_id=cohort.id)

    def test_re_request_allowed_after_cooldown_expires(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_refused_consent"):
            CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.REFUSED,
                decided_at=timezone.now() - timedelta(days=8),
            )

        consent = request_consent(counselor=counselor, student=student, cohort_id=cohort.id)

        assert consent.status == CounselorConsentStatus.PENDING


class TestStudentDecidesConsent:
    def test_student_lists_own_pending_requests(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_consent"):
            CounselorConsent.objects.create(student=student, counselor=counselor, cohort=cohort)
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.get(reverse("establishments_cohort:student-pending-consents"))

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["counselor_email"] == counselor.email

    def test_student_grants_consent(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_consent"):
            consent = CounselorConsent.objects.create(
                student=student, counselor=counselor, cohort=cohort
            )
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.post(
            reverse(
                "establishments_cohort:student-decide-consent",
                kwargs={"consent_id": consent.id},
            ),
            {"granted": True},
            format="json",
        )

        assert response.status_code == 200, response.content
        assert response.json()["status"] == "granted"

    def test_student_refuses_consent(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_consent"):
            consent = CounselorConsent.objects.create(
                student=student, counselor=counselor, cohort=cohort
            )
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.post(
            reverse(
                "establishments_cohort:student-decide-consent",
                kwargs={"consent_id": consent.id},
            ),
            {"granted": False},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["status"] == "refused"

    def test_cannot_decide_another_students_request(self):
        counselor, student, cohort = _setup()
        intruder = _uf(email="intruder-consent@test.local", role=UserRole.STUDENT)
        with bypass_rls(reason="test_setup.create_consent"):
            consent = CounselorConsent.objects.create(
                student=student, counselor=counselor, cohort=cohort
            )
        client = APIClient()
        client.force_authenticate(user=intruder)

        response = client.post(
            reverse(
                "establishments_cohort:student-decide-consent",
                kwargs={"consent_id": consent.id},
            ),
            {"granted": True},
            format="json",
        )

        assert response.status_code == 404

    def test_deciding_an_already_decided_request_returns_409(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_consent"):
            consent = CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
            )
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.post(
            reverse(
                "establishments_cohort:student-decide-consent",
                kwargs={"consent_id": consent.id},
            ),
            {"granted": False},
            format="json",
        )

        assert response.status_code == 409


class TestCounselorConsentAccessListIntegration:
    """Story 6.11 seam — granted consent appears in the unified access list."""

    def test_granted_consent_appears_in_access_list(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_consent"):
            CounselorConsent.objects.create(
                student=student,
                counselor=counselor,
                cohort=cohort,
                status=CounselorConsentStatus.GRANTED,
                decided_at=timezone.now(),
            )

        entries = AccessListAggregator(sources=[CounselorConsentSource()]).list_for_user(student)

        assert len(entries) == 1
        assert entries[0].tier_type == "counselor"
        assert entries[0].display_name == counselor.email

    def test_pending_or_revoked_consent_does_not_appear(self):
        counselor, student, cohort = _setup()
        with bypass_rls(reason="test_setup.create_consent"):
            CounselorConsent.objects.create(student=student, counselor=counselor, cohort=cohort)

        entries = AccessListAggregator(sources=[CounselorConsentSource()]).list_for_user(student)

        assert entries == []
