"""School-side reception tests — Story 5.6.

Covers:
- GET /api/v1/ecole/outreach/       — reception queue, school-scoped (AC)
- GET /api/v1/ecole/outreach/{id}/  — detail, school-scoped, RBAC boundary
- `expire_stale_early_outreach_requests` — the 7-day expiry Celery task
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachRequestStatus
from apps.outreach.tasks import expire_stale_early_outreach_requests
from apps.professions.models import Profession
from apps.schools.models import School, SchoolStaff

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_reception_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


@pytest.fixture
def student() -> User:
    return _uf(email="eleve-reception@test.local", role=UserRole.STUDENT)


@pytest.fixture
def school(db) -> School:
    return School.objects.create(
        slug="ecole-reception-test",
        name="École Réception Test",
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
def other_school(db) -> School:
    return School.objects.create(
        slug="autre-ecole-reception-test",
        name="Autre École Test",
        type=School.Type.UNIVERSITE,
        city="Paris",
        region="Île-de-France",
        postal_code="75000",
        selectivity_index=3,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
    )


@pytest.fixture
def profession(db) -> Profession:
    return Profession.objects.create(
        slug="metier-reception-test",
        name="Métier Réception Test",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )


@pytest.fixture
def school_admin(school) -> User:
    user = _uf(email="admin-ecole@test.local", role=UserRole.SCHOOL_ADMIN)
    with bypass_rls(reason="test_setup.link_school_staff"):
        SchoolStaff.objects.create(user=user, school=school)
    # `IsSchoolAdmin.requires_mfa_verified=True` checks `user.is_verified()`,
    # a method django-otp's OTPMiddleware attaches after a real OTP
    # challenge — `force_authenticate` skips that middleware entirely.
    # Monkeypatching the instance method is the pattern this repo already
    # uses for permission-class unit tests (apps/core/tests/test_rbac_
    # permissions.py); MFA enrollment itself is Story 1.6's concern, already
    # covered there, not re-tested per-role here.
    user.is_verified = lambda: True
    return user


@pytest.fixture
def school_admin_client(school_admin) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=school_admin)
    return client


def _create_outreach(
    *, student, school, profession, status=EarlyOutreachRequestStatus.PENDING, **kwargs
) -> EarlyOutreachRequest:
    with bypass_rls(reason="test_setup.create_outreach"):
        return EarlyOutreachRequest.objects.create(
            student=student, school=school, profession=profession, status=status, **kwargs
        )


class TestEcoleOutreachQueue:
    def test_lists_only_requests_sent_to_the_admins_school(
        self, school_admin_client, student, school, other_school, profession
    ):
        mine = _create_outreach(student=student, school=school, profession=profession)
        _create_outreach(student=student, school=other_school, profession=profession)

        response = school_admin_client.get(reverse("outreach:ecole-outreach-queue"))

        assert response.status_code == 200, response.content
        ids = [row["id"] for row in response.json()["results"]]
        assert ids == [mine.id]

    def test_hides_pending_moderation_and_rejected_requests(
        self, school_admin_client, student, school, profession
    ):
        _create_outreach(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.PENDING_MODERATION,
        )
        _create_outreach(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.REJECTED,
        )

        response = school_admin_client.get(reverse("outreach:ecole-outreach-queue"))

        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_does_not_expose_student_identity_beyond_age(
        self, school_admin_client, student, school, profession
    ):
        _create_outreach(student=student, school=school, profession=profession)

        response = school_admin_client.get(reverse("outreach:ecole-outreach-queue"))

        row = response.json()["results"][0]
        assert "student_id" not in row
        assert "email" not in row
        assert "student" not in row

    def test_filters_by_status(self, school_admin_client, student, school, profession):
        _create_outreach(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.RESPONDED,
        )
        _create_outreach(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.PENDING,
        )

        response = school_admin_client.get(
            reverse("outreach:ecole-outreach-queue"), {"status": "responded"}
        )

        assert response.status_code == 200
        assert [r["status"] for r in response.json()["results"]] == ["responded"]

    def test_student_cannot_access_the_ecole_queue(self, student, school, profession):
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.get(reverse("outreach:ecole-outreach-queue"))

        assert response.status_code == 403

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(reverse("outreach:ecole-outreach-queue"))
        assert response.status_code == 401


class TestEcoleOutreachDetail:
    def test_shows_motivation_and_profession_for_own_school(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(
            student=student,
            school=school,
            profession=profession,
            motivation_text="Un texte de motivation.",
        )

        response = school_admin_client.get(
            reverse("outreach:ecole-outreach-detail", kwargs={"outreach_id": outreach.id})
        )

        assert response.status_code == 200, response.content
        body = response.json()
        assert body["motivation_text"] == "Un texte de motivation."
        assert body["profession_name"] == profession.name

    def test_returns_404_for_another_schools_request(
        self, school_admin_client, student, other_school, profession
    ):
        outreach = _create_outreach(student=student, school=other_school, profession=profession)

        response = school_admin_client.get(
            reverse("outreach:ecole-outreach-detail", kwargs={"outreach_id": outreach.id})
        )

        assert response.status_code == 404

    def test_returns_404_for_a_pending_moderation_request(
        self, school_admin_client, student, school, profession
    ):
        outreach = _create_outreach(
            student=student,
            school=school,
            profession=profession,
            status=EarlyOutreachRequestStatus.PENDING_MODERATION,
        )

        response = school_admin_client.get(
            reverse("outreach:ecole-outreach-detail", kwargs={"outreach_id": outreach.id})
        )

        assert response.status_code == 404


class TestSchoolStaffNotLinked:
    def test_school_admin_without_a_school_link_gets_403(self, school, profession, student):
        unlinked_admin = _uf(email="admin-sans-ecole@test.local", role=UserRole.SCHOOL_ADMIN)
        unlinked_admin.is_verified = lambda: True
        client = APIClient()
        client.force_authenticate(user=unlinked_admin)

        response = client.get(reverse("outreach:ecole-outreach-queue"))

        assert response.status_code == 403


# ── Story 5.6 — 7-day expiry Celery task ─────────────────────────────────────


class TestExpireStaleRequests:
    def test_expires_pending_requests_older_than_7_days_and_notifies(
        self, student, school, profession
    ):
        stale = _create_outreach(student=student, school=school, profession=profession)
        with bypass_rls(reason="test_setup.backdate_outreach"):
            EarlyOutreachRequest.objects.filter(id=stale.id).update(
                created_at=timezone.now() - timedelta(days=8)
            )
        fresh = _create_outreach(student=student, school=school, profession=profession)

        count = expire_stale_early_outreach_requests()

        assert count == 1
        with bypass_rls(reason="test_assert.read_outreach"):
            stale.refresh_from_db()
            fresh.refresh_from_db()
        assert stale.status == EarlyOutreachRequestStatus.EXPIRED_7D
        assert fresh.status == EarlyOutreachRequestStatus.PENDING
        assert len(mail.outbox) == 1
        assert (
            "pas répondu" in mail.outbox[0].subject.lower()
            or "pas répondu" in mail.outbox[0].body.lower()
        )

    def test_does_not_touch_already_responded_or_moderated_requests(
        self, student, school, profession
    ):
        with bypass_rls(reason="test_setup.backdate_outreach"):
            responded = _create_outreach(
                student=student,
                school=school,
                profession=profession,
                status=EarlyOutreachRequestStatus.RESPONDED,
            )
            EarlyOutreachRequest.objects.filter(id=responded.id).update(
                created_at=timezone.now() - timedelta(days=8)
            )
            moderation = _create_outreach(
                student=student,
                school=school,
                profession=profession,
                status=EarlyOutreachRequestStatus.PENDING_MODERATION,
            )
            EarlyOutreachRequest.objects.filter(id=moderation.id).update(
                created_at=timezone.now() - timedelta(days=8)
            )

        count = expire_stale_early_outreach_requests()

        assert count == 0
