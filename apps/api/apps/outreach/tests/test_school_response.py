"""School-response tests — Story 5.7.

Covers:
- POST /api/v1/ecole/outreach/{id}/respond/            — the school's 3 actions
- POST /api/v1/outreach/requests/{id}/interview/accept/       — student accepts a slot
- POST /api/v1/outreach/requests/{id}/interview/alternative/  — student proposes another
"""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachRequestStatus,
    EarlyOutreachResponse,
    EarlyOutreachResponseAction,
)
from apps.professions.models import Profession
from apps.schools.models import AdmissionStat, School, SchoolStaff

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_response_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


@pytest.fixture
def student() -> User:
    return _uf(email="eleve-reponse@test.local", role=UserRole.STUDENT)


@pytest.fixture
def student_client(student) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=student)
    return client


@pytest.fixture
def school(db) -> School:
    return School.objects.create(
        slug="ecole-reponse-test",
        name="École Réponse Test",
        type=School.Type.ECOLE_INGENIEUR,
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
        postal_code="69000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
    )


@pytest.fixture
def profession(db) -> Profession:
    return Profession.objects.create(
        slug="metier-reponse-test",
        name="Métier Réponse Test",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )


@pytest.fixture
def school_admin(school) -> User:
    user = _uf(email="admin-ecole-reponse@test.local", role=UserRole.SCHOOL_ADMIN)
    with bypass_rls(reason="test_setup.link_school_staff"):
        SchoolStaff.objects.create(user=user, school=school)
    user.is_verified = lambda: True  # see test_school_reception.py for rationale
    return user


@pytest.fixture
def school_admin_client(school_admin) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=school_admin)
    return client


def _create_outreach(*, student, school, profession, **kwargs) -> EarlyOutreachRequest:
    with bypass_rls(reason="test_setup.create_outreach"):
        return EarlyOutreachRequest.objects.create(
            student=student, school=school, profession=profession, **kwargs
        )


def _words(n: int) -> str:
    return " ".join(["mot"] * n)


class TestEcoleOutreachRespond:
    def test_interested_response_flips_status_and_notifies_student(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "interested", "comment": "Beau profil, on encourage ta candidature."},
            format="json",
        )

        assert response.status_code == 201, response.content
        with bypass_rls(reason="test_assert.read_outreach"):
            outreach.refresh_from_db()
        assert outreach.status == EarlyOutreachRequestStatus.RESPONDED
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [student.email]

    def test_not_aligned_response(self, school_admin_client, student, school, profession):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "not_aligned"},
            format="json",
        )

        assert response.status_code == 201, response.content
        assert response.json()["response"]["action"] == "not_aligned"

    def test_interview_requested_requires_2_to_3_slots(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        too_few = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "interview_requested", "proposed_slots": ["2026-10-01T10:00:00Z"]},
            format="json",
        )
        assert too_few.status_code == 400

        ok = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {
                "action": "interview_requested",
                "proposed_slots": ["2026-10-01T10:00:00Z", "2026-10-02T14:00:00Z"],
            },
            format="json",
        )
        assert ok.status_code == 201, ok.content
        assert ok.json()["response"]["proposed_slots"] == [
            "2026-10-01T10:00:00Z",
            "2026-10-02T14:00:00Z",
        ]

    def test_slots_rejected_for_non_interview_actions(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "interested", "proposed_slots": ["2026-10-01T10:00:00Z"]},
            format="json",
        )

        assert response.status_code == 400

    def test_comment_over_200_words_is_rejected(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "interested", "comment": _words(201)},
            format="json",
        )

        assert response.status_code == 400

    def test_responding_twice_returns_409(self, school_admin_client, student, school, profession):
        outreach = _create_outreach(student=student, school=school, profession=profession)
        url = reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id})
        first = school_admin_client.post(url, {"action": "interested"}, format="json")
        assert first.status_code == 201, first.content

        second = school_admin_client.post(url, {"action": "not_aligned"}, format="json")

        assert second.status_code == 409, second.content

    def test_cannot_respond_to_another_schools_request(
        self, school_admin_client, student, profession
    ):
        other_school = School.objects.create(
            slug="autre-ecole-reponse-test",
            name="Autre École Réponse Test",
            type=School.Type.UNIVERSITE,
            city="Paris",
            region="Île-de-France",
            postal_code="75000",
            selectivity_index=3,
            public_private=School.PublicPrivate.PUBLIC,
            description="x" * 20,
            official_url="https://test.example",
        )
        outreach = _create_outreach(student=student, school=other_school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "interested"},
            format="json",
        )

        assert response.status_code == 404


class TestInterviewFollowUp:
    def _outreach_with_interview(self, student, school, profession) -> EarlyOutreachRequest:
        outreach = _create_outreach(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.RESPONDED,
        )
        with bypass_rls(reason="test_setup.create_response"):
            EarlyOutreachResponse.objects.create(
                request=outreach,
                action=EarlyOutreachResponseAction.INTERVIEW_REQUESTED,
                proposed_slots=["2026-10-01T10:00:00Z", "2026-10-02T14:00:00Z"],
            )
        return outreach

    def test_student_accepts_a_proposed_slot(
        self, student_client, student, school, profession, school_admin
    ):
        outreach = self._outreach_with_interview(student, school, profession)

        response = student_client.post(
            reverse("outreach:interview-accept", kwargs={"outreach_id": outreach.id}),
            {"slot": "2026-10-01T10:00:00Z"},
            format="json",
        )

        assert response.status_code == 200, response.content
        assert response.json()["response"]["accepted_slot"] == "2026-10-01T10:00:00Z"
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [school_admin.email]

    def test_accepting_a_slot_not_proposed_returns_400(
        self, student_client, student, school, profession
    ):
        outreach = self._outreach_with_interview(student, school, profession)

        response = student_client.post(
            reverse("outreach:interview-accept", kwargs={"outreach_id": outreach.id}),
            {"slot": "2099-01-01T00:00:00Z"},
            format="json",
        )

        assert response.status_code == 400

    def test_student_proposes_an_alternative(
        self, student_client, student, school, profession, school_admin
    ):
        outreach = self._outreach_with_interview(student, school, profession)

        response = student_client.post(
            reverse("outreach:interview-alternative", kwargs={"outreach_id": outreach.id}),
            {"note": "Je ne suis dispo qu'après 16h, possible ?"},
            format="json",
        )

        assert response.status_code == 200, response.content
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [school_admin.email]

    def test_cannot_accept_twice(self, student_client, student, school, profession, school_admin):
        outreach = self._outreach_with_interview(student, school, profession)
        url = reverse("outreach:interview-accept", kwargs={"outreach_id": outreach.id})
        first = student_client.post(url, {"slot": "2026-10-01T10:00:00Z"}, format="json")
        assert first.status_code == 200, first.content

        second = student_client.post(url, {"slot": "2026-10-02T14:00:00Z"}, format="json")

        assert second.status_code == 409, second.content

    def test_another_student_cannot_touch_this_interview(self, school, profession):
        owner = _uf(email="eleve-proprio@test.local", role=UserRole.STUDENT)
        intruder = _uf(email="eleve-intrus@test.local", role=UserRole.STUDENT)
        outreach = self._outreach_with_interview(owner, school, profession)

        client = APIClient()
        client.force_authenticate(user=intruder)
        response = client.post(
            reverse("outreach:interview-accept", kwargs={"outreach_id": outreach.id}),
            {"slot": "2026-10-01T10:00:00Z"},
            format="json",
        )

        assert response.status_code == 404


class TestStatPropagation:
    """Story 5.8 — responding nudges the student's AdmissionStat for that school."""

    def test_interested_response_nudges_the_stat_up(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "interested"},
            format="json",
        )

        assert response.status_code == 201, response.content
        with bypass_rls(reason="test_assert.read_stat"):
            stat = AdmissionStat.objects.get(school=school, user=student)
        assert stat.outreach_delta_applied_at is not None
        assert stat.expected_proba > stat.previous_proba

    def test_not_aligned_response_nudges_the_stat_down(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {"action": "not_aligned"},
            format="json",
        )

        assert response.status_code == 201, response.content
        with bypass_rls(reason="test_assert.read_stat"):
            stat = AdmissionStat.objects.get(school=school, user=student)
        assert stat.expected_proba < stat.previous_proba

    def test_response_serializer_exposes_the_stat_delta(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.post(
            reverse("outreach:ecole-outreach-respond", kwargs={"outreach_id": outreach.id}),
            {
                "action": "interview_requested",
                "proposed_slots": ["2026-10-01T10:00:00Z", "2026-10-02T14:00:00Z"],
            },
            format="json",
        )

        assert response.status_code == 201, response.content
        assert response.json()["response"]["stat_delta"] == 7
