"""Counselor individual profile view tests — Story 6.8.

Covers:
- GET  /api/v1/establishments/students/{id}/profile/            — AC1
- GET/POST /api/v1/establishments/students/{id}/notes/           — AC2 (private notes)
- GET  /api/v1/establishments/students/{id}/interview-sheet.pdf/ — AC2 (export)
- 403 without a granted consent
- `touch_last_accessed` + audit-trail assertions
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.core.rls import bypass_rls
from apps.establishments.models import (
    Cohort,
    CounselorConsent,
    CounselorConsentStatus,
    CounselorNote,
    EstablishmentType,
    LicenseType,
    StudentImportInvitation,
    StudentImportInvitationStatus,
)
from apps.establishments.models import Establishment as EstablishmentModel

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mock_ai_recommendations():
    """`get_student_profile_for_counselor` reuses `get_child_professions`,
    which calls the ai-service over HTTP — mocked out the same way
    `test_parent_child_detail_views.py` mocks it, since these tests only
    care about the profile/notes/consent plumbing, not scoring itself."""
    with patch("apps.family.services.parent_view.compute_recommendations") as mock_reco:
        mock_reco.return_value = {"results": []}
        yield mock_reco


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_profile_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


_uai_counter = iter(range(1000, 2000))


def _establishment() -> EstablishmentModel:
    n = next(_uai_counter)
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentModel.objects.create(
            name=f"Lycée Profile Test {n}",
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


def _granted_consent(*, student, counselor, cohort) -> CounselorConsent:
    with bypass_rls(reason="test_setup.create_granted_consent"):
        return CounselorConsent.objects.create(
            student=student,
            counselor=counselor,
            cohort=cohort,
            status=CounselorConsentStatus.GRANTED,
            decided_at=timezone.now(),
        )


def _setup(*, with_consent: bool = True):
    establishment = _establishment()
    cohort = _cohort(establishment)
    counselor = _uf(
        email="counselor-profile@test.local", role=UserRole.COUNSELOR, tenant_id=establishment.id
    )
    # `IsCounselor.requires_mfa_verified=True` checks `user.is_verified()`,
    # a method django-otp's OTPMiddleware attaches after a real OTP
    # challenge — `force_authenticate` skips that middleware entirely. Same
    # monkeypatch pattern as `test_counselor_consent.py`.
    counselor.is_verified = lambda: True
    student = _uf(email="student-profile@test.local", role=UserRole.STUDENT)
    _accepted_invitation(cohort=cohort, student=student)
    consent = (
        _granted_consent(student=student, counselor=counselor, cohort=cohort)
        if with_consent
        else None
    )
    return counselor, student, cohort, consent


class TestCounselorStudentProfile:
    def test_profile_returns_200_with_granted_consent(self):
        counselor, student, cohort, _ = _setup()
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(
            reverse(
                "establishments_cohort:counselor-student-profile",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 200, response.content
        body = response.json()
        assert body["student_id"] == student.id
        assert body["cohort_name"] == cohort.name
        assert body["metiers_top_recos"] == []
        assert body["mes_paris"] == []
        assert body["voeux_en_construction"] == []
        assert "derniere_connexion" in body["activite_recente"]

    def test_profile_returns_403_without_granted_consent(self):
        counselor, student, _, _ = _setup(with_consent=False)
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(
            reverse(
                "establishments_cohort:counselor-student-profile",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 403

    def test_profile_view_stamps_last_accessed_and_audit_log(self):
        counselor, student, _cohort, consent = _setup()
        client = APIClient()
        client.force_authenticate(user=counselor)

        assert consent.last_accessed_at is None

        response = client.get(
            reverse(
                "establishments_cohort:counselor-student-profile",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 200
        with bypass_rls(reason="test_assert.reload_consent"):
            consent.refresh_from_db()
        assert consent.last_accessed_at is not None

        with bypass_rls(reason="test_assert.read_audit_log"):
            log = AuditLog.objects.filter(action="establishments.counselor_profile_viewed").latest(
                "created_at"
            )
        assert log.subject_id == student.id


class TestCounselorNotes:
    def test_counselor_can_add_and_list_private_notes(self):
        counselor, student, _, _ = _setup()
        client = APIClient()
        client.force_authenticate(user=counselor)
        url = reverse(
            "establishments_cohort:counselor-student-notes",
            kwargs={"student_id": student.id},
        )

        create_response = client.post(url, {"text": "Bon relationnel, motivé."}, format="json")
        assert create_response.status_code == 201, create_response.content

        list_response = client.get(url)
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
        assert list_response.json()[0]["text"] == "Bon relationnel, motivé."

    def test_notes_require_granted_consent(self):
        counselor, student, _, _ = _setup(with_consent=False)
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(
            reverse(
                "establishments_cohort:counselor-student-notes",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 403

    def test_notes_are_private_to_the_authoring_counselor(self):
        counselor, student, cohort, _ = _setup()
        other_counselor = _uf(
            email="counselor-other-profile@test.local",
            role=UserRole.COUNSELOR,
            tenant_id=counselor.tenant_id,
        )
        other_counselor.is_verified = lambda: True
        _granted_consent(student=student, counselor=other_counselor, cohort=cohort)
        with bypass_rls(reason="test_setup.create_note"):
            CounselorNote.objects.create(counselor=counselor, student=student, text="Note privée")

        client = APIClient()
        client.force_authenticate(user=other_counselor)
        response = client.get(
            reverse(
                "establishments_cohort:counselor-student-notes",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 200
        assert response.json() == []


class TestCounselorInterviewSheetPdf:
    def test_pdf_export_returns_valid_pdf_bytes(self):
        counselor, student, _, _ = _setup()
        with bypass_rls(reason="test_setup.create_note"):
            CounselorNote.objects.create(counselor=counselor, student=student, text="RAS")
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(
            reverse(
                "establishments_cohort:counselor-interview-sheet-pdf",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        assert f'filename="fiche-entretien-{student.id}.pdf"' in response["Content-Disposition"]

    def test_pdf_export_requires_granted_consent(self):
        counselor, student, _, _ = _setup(with_consent=False)
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(
            reverse(
                "establishments_cohort:counselor-interview-sheet-pdf",
                kwargs={"student_id": student.id},
            )
        )

        assert response.status_code == 403
