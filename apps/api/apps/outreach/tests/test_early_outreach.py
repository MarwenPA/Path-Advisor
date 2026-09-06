"""Early-outreach request tests — Stories 5.4 + 5.5.

Covers:
- POST /api/v1/schools/{slug}/outreach/  — create (AC2/AC3/AC5)
- GET  /api/v1/outreach/requests/        — list (AC4)
- GET  /api/v1/outreach/quota/           — AC1/AC3
- Story 5.5 — motivation word-count validation, moderation gate (create),
  approve/reject service functions, resubmit endpoint.
"""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.billing.models import Subscription
from apps.core.rls import bypass_rls
from apps.outreach.exceptions import OutreachModerationStateError
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachRequestStatus
from apps.outreach.services.early_outreach import (
    MONTHLY_QUOTA,
    approve_early_outreach_motivation,
    reject_early_outreach_motivation,
)
from apps.professions.models import Profession
from apps.schools.models import Parcours, School

pytestmark = pytest.mark.django_db


def _words(n: int) -> str:
    return " ".join(["mot"] * n)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_outreach_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


@pytest.fixture
def premium_student() -> User:
    user = _uf(email="premium-eleve@test.local")
    with bypass_rls(reason="test_setup.create_subscription"):
        Subscription.objects.create(user=user, tier="premium", status="active")
    return user


@pytest.fixture
def free_student() -> User:
    return _uf(email="free-eleve@test.local")


@pytest.fixture
def premium_client(premium_student) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=premium_student)
    return client


@pytest.fixture
def free_client(free_student) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=free_student)
    return client


@pytest.fixture
def school(db) -> School:
    return School.objects.create(
        slug="ecole-outreach-test",
        name="École Outreach Test",
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
        slug="metier-outreach-test",
        name="Métier Outreach Test",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )


def _url(school_slug: str) -> str:
    return reverse("outreach:school-outreach-create", kwargs={"slug": school_slug})


# ── AC2/AC5 — create ─────────────────────────────────────────────────────────


class TestCreateEarlyOutreachRequest:
    def test_premium_student_creates_a_pending_request(self, premium_client, school, profession):
        response = premium_client.post(
            _url(school.slug), {"profession_id": profession.id}, format="json"
        )

        assert response.status_code == 201, response.content
        with bypass_rls(reason="test_assert.read_outreach"):
            outreach = EarlyOutreachRequest.objects.get(id=response.json()["id"])
        assert outreach.status == EarlyOutreachRequestStatus.PENDING
        assert outreach.school_id == school.id
        assert outreach.profession_id == profession.id
        assert outreach.motivation_text == ""

    def test_accepts_a_valid_motivation_and_gates_it_into_pending_moderation(
        self, premium_client, school, profession
    ):
        """Story 5.5 — a well-formed (200-500 word) motivation blocks the
        send until moderation, and triggers the "en cours de relecture" email."""
        response = premium_client.post(
            _url(school.slug),
            {"profession_id": profession.id, "motivation_text": _words(200)},
            format="json",
        )
        assert response.status_code == 201, response.content
        assert response.json()["status"] == EarlyOutreachRequestStatus.PENDING_MODERATION
        assert len(mail.outbox) == 1
        assert "relecture" in mail.outbox[0].subject.lower()

    def test_motivation_below_200_words_is_rejected(self, premium_client, school, profession):
        response = premium_client.post(
            _url(school.slug),
            {"profession_id": profession.id, "motivation_text": _words(199)},
            format="json",
        )
        assert response.status_code == 400, response.content

    def test_motivation_above_500_words_is_rejected(self, premium_client, school, profession):
        response = premium_client.post(
            _url(school.slug),
            {"profession_id": profession.id, "motivation_text": _words(501)},
            format="json",
        )
        assert response.status_code == 400, response.content

    def test_resolves_default_parcours_server_side(self, premium_client, school, profession):
        with bypass_rls(reason="test_setup.create_parcours"):
            parcours = Parcours.objects.create(
                profession=profession, target_school=school, is_default=True
            )

        response = premium_client.post(
            _url(school.slug), {"profession_id": profession.id}, format="json"
        )

        assert response.status_code == 201, response.content
        with bypass_rls(reason="test_assert.read_outreach"):
            outreach = EarlyOutreachRequest.objects.get(id=response.json()["id"])
        assert outreach.parcours_id == parcours.id

    def test_freemium_student_gets_402(self, free_client, school, profession):
        """AC5 — a UI bypass (direct API call) is rejected with the typed
        InsufficientPlan, not a generic 403."""
        response = free_client.post(
            _url(school.slug), {"profession_id": profession.id}, format="json"
        )
        assert response.status_code == 402, response.content

    def test_unauthenticated_returns_401(self, school, profession):
        client = APIClient()
        response = client.post(_url(school.slug), {"profession_id": profession.id}, format="json")
        assert response.status_code == 401

    def test_unknown_school_returns_404(self, premium_client, profession):
        response = premium_client.post(
            reverse("outreach:school-outreach-create", kwargs={"slug": "ecole-inexistante"}),
            {"profession_id": profession.id},
            format="json",
        )
        assert response.status_code == 404

    def test_inactive_profession_returns_404(self, premium_client, school, profession):
        with bypass_rls(reason="test_setup.deactivate_profession"):
            profession.is_active = False
            profession.save(update_fields=["is_active"])

        response = premium_client.post(
            _url(school.slug), {"profession_id": profession.id}, format="json"
        )
        assert response.status_code == 404


# ── AC3 — monthly quota ──────────────────────────────────────────────────────


class TestMonthlyQuota:
    def test_quota_view_reflects_usage(self, premium_client, school, profession):
        response = premium_client.get(reverse("outreach:quota"))
        assert response.status_code == 200
        assert response.json() == {"used": 0, "limit": MONTHLY_QUOTA, "remaining": MONTHLY_QUOTA}

        premium_client.post(_url(school.slug), {"profession_id": profession.id}, format="json")

        response = premium_client.get(reverse("outreach:quota"))
        assert response.json() == {
            "used": 1,
            "limit": MONTHLY_QUOTA,
            "remaining": MONTHLY_QUOTA - 1,
        }

    def test_6th_request_this_month_returns_429_with_non_scary_copy(
        self, premium_client, premium_student, school, profession
    ):
        with bypass_rls(reason="test_setup.fill_quota"):
            for i in range(MONTHLY_QUOTA):
                other_school = School.objects.create(
                    slug=f"ecole-quota-{i}",
                    name=f"École Quota {i}",
                    type=School.Type.UNIVERSITE,
                    city="Paris",
                    region="Île-de-France",
                    postal_code="75000",
                    selectivity_index=3,
                    public_private=School.PublicPrivate.PUBLIC,
                    description="x" * 20,
                    official_url="https://test.example",
                )
                EarlyOutreachRequest.objects.create(
                    student=premium_student, school=other_school, profession=profession
                )

        response = premium_client.post(
            _url(school.slug), {"profession_id": profession.id}, format="json"
        )

        assert response.status_code == 429, response.content
        assert "5 envois" in response.json()["detail"]
        assert "1er du mois prochain" in response.json()["detail"]


# ── AC4 — list ───────────────────────────────────────────────────────────────


class TestListEarlyOutreachRequests:
    def test_lists_only_the_current_students_requests(
        self, premium_client, premium_student, school, profession
    ):
        other_student = _uf(email="autre-eleve@test.local")
        with bypass_rls(reason="test_setup.create_outreach"):
            mine = EarlyOutreachRequest.objects.create(
                student=premium_student, school=school, profession=profession
            )
            EarlyOutreachRequest.objects.create(
                student=other_student, school=school, profession=profession
            )

        response = premium_client.get(reverse("outreach:request-list"))

        assert response.status_code == 200
        ids = [row["id"] for row in response.json()["results"]]
        assert ids == [mine.id]

    def test_empty_list_for_a_student_with_no_requests(self, premium_client):
        response = premium_client.get(reverse("outreach:request-list"))
        assert response.status_code == 200
        assert response.json()["results"] == []


# ── Story 5.5 — moderation service functions ─────────────────────────────────


class TestModerationServiceFunctions:
    def _pending_moderation_outreach(self, student, school, profession) -> EarlyOutreachRequest:
        with bypass_rls(reason="test_setup.create_outreach"):
            return EarlyOutreachRequest.objects.create(
                student=student,
                school=school,
                profession=profession,
                motivation_text=_words(250),
                status=EarlyOutreachRequestStatus.PENDING_MODERATION,
            )

    def test_approve_unblocks_the_request_and_notifies(self, premium_student, school, profession):
        outreach = self._pending_moderation_outreach(premium_student, school, profession)

        result = approve_early_outreach_motivation(outreach=outreach)

        assert result.status == EarlyOutreachRequestStatus.PENDING
        assert len(mail.outbox) == 1
        assert "route" in mail.outbox[0].subject.lower()

    def test_approve_twice_raises_moderation_state_error(self, premium_student, school, profession):
        outreach = self._pending_moderation_outreach(premium_student, school, profession)
        approve_early_outreach_motivation(outreach=outreach)
        outreach.refresh_from_db()

        with pytest.raises(OutreachModerationStateError):
            approve_early_outreach_motivation(outreach=outreach)

    def test_reject_blocks_and_records_the_reason(self, premium_student, school, profession):
        outreach = self._pending_moderation_outreach(premium_student, school, profession)

        result = reject_early_outreach_motivation(
            outreach=outreach, reason="Trop générique, précise ton projet."
        )

        assert result.status == EarlyOutreachRequestStatus.REJECTED
        assert result.rejection_reason == "Trop générique, précise ton projet."
        assert len(mail.outbox) == 1
        assert "Trop générique" in mail.outbox[0].body


# ── Story 5.5 — resubmit endpoint ────────────────────────────────────────────


class TestResubmitEarlyOutreach:
    def _rejected_outreach(self, student, school, profession) -> EarlyOutreachRequest:
        with bypass_rls(reason="test_setup.create_outreach"):
            return EarlyOutreachRequest.objects.create(
                student=student,
                school=school,
                profession=profession,
                motivation_text=_words(250),
                status=EarlyOutreachRequestStatus.REJECTED,
                rejection_reason="Trop générique.",
            )

    def test_student_can_resubmit_a_rejected_motivation(
        self, premium_client, premium_student, school, profession
    ):
        outreach = self._rejected_outreach(premium_student, school, profession)

        response = premium_client.post(
            reverse("outreach:request-resubmit", kwargs={"outreach_id": outreach.id}),
            {"motivation_text": _words(220)},
            format="json",
        )

        assert response.status_code == 200, response.content
        assert response.json()["status"] == EarlyOutreachRequestStatus.PENDING_MODERATION
        assert response.json()["rejection_reason"] == ""

    def test_resubmit_requires_200_to_500_words(
        self, premium_client, premium_student, school, profession
    ):
        outreach = self._rejected_outreach(premium_student, school, profession)

        response = premium_client.post(
            reverse("outreach:request-resubmit", kwargs={"outreach_id": outreach.id}),
            {"motivation_text": _words(10)},
            format="json",
        )

        assert response.status_code == 400, response.content

    def test_resubmit_on_a_non_rejected_request_returns_409(
        self, premium_client, premium_student, school, profession
    ):
        with bypass_rls(reason="test_setup.create_outreach"):
            outreach = EarlyOutreachRequest.objects.create(
                student=premium_student,
                school=school,
                profession=profession,
                status=EarlyOutreachRequestStatus.PENDING,
            )

        response = premium_client.post(
            reverse("outreach:request-resubmit", kwargs={"outreach_id": outreach.id}),
            {"motivation_text": _words(220)},
            format="json",
        )

        assert response.status_code == 409, response.content

    def test_student_cannot_resubmit_another_students_request(
        self, premium_client, school, profession
    ):
        other_student = _uf(email="autre-eleve-2@test.local")
        outreach = self._rejected_outreach(other_student, school, profession)

        response = premium_client.post(
            reverse("outreach:request-resubmit", kwargs={"outreach_id": outreach.id}),
            {"motivation_text": _words(220)},
            format="json",
        )

        assert response.status_code == 404


# ── Story 5.9 — student-facing detail view ──────────────────────────────────


class TestEarlyOutreachDetailView:
    def test_shows_motivation_and_school_slug(
        self, premium_client, premium_student, school, profession
    ):
        with bypass_rls(reason="test_setup.create_outreach"):
            outreach = EarlyOutreachRequest.objects.create(
                student=premium_student,
                school=school,
                profession=profession,
                motivation_text="Ma motivation.",
            )

        response = premium_client.get(
            reverse("outreach:request-detail", kwargs={"outreach_id": outreach.id})
        )

        assert response.status_code == 200, response.content
        body = response.json()
        assert body["motivation_text"] == "Ma motivation."
        assert body["school_slug"] == school.slug

    def test_another_students_request_returns_404(self, premium_client, school, profession):
        other_student = _uf(email="autre-eleve-3@test.local")
        with bypass_rls(reason="test_setup.create_outreach"):
            outreach = EarlyOutreachRequest.objects.create(
                student=other_student, school=school, profession=profession
            )

        response = premium_client.get(
            reverse("outreach:request-detail", kwargs={"outreach_id": outreach.id})
        )

        assert response.status_code == 404
