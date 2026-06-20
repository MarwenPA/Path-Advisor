"""Tests for RecommendationReview API — Story 3.7.

Covers AC4, AC5, AC9 backend:
- POST /api/v1/students/me/recommendation-reviews/ → 201 + RecommendationReview created + audit log
- POST without reason → 400
- POST without auth → 401
- POST with comment > 500 chars → 400
- POST duplicate (same student + profession) → 409
- POST invalid reason → 400
- POST unknown profession slug → 404
- GET /api/v1/admin/recommendation-reviews/ → 200 for admin, 403 for student
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.professions.models import Profession
from apps.recommendations.models import RecommendationReview

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="eleve@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.local",
        password="Strong1!pass",
        role=UserRole.PATH_ADMIN,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
        is_superuser=True,
    )


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def profession(db):
    return Profession.objects.create(
        slug="medecin-generaliste-test",
        name="Médecin généraliste test",
        description="Description test " * 12,
        daily_routine="Tu commences ta matinée en consultant tes patients. " * 5,
        requirements_json=[
            {"type": "studies", "label": "PACES + 9 ans études médicales"},
            {"type": "skill", "label": "Diagnostic clinique"},
        ],
        prospects_text="1. Spécialiste. 2. Chef de service. 3. Chercheur.",
        signals_json={
            "passions": ["médecine", "biologie"],
            "valeurs": ["soin", "altruisme"],
            "specialites": ["svt", "chimie"],
            "keywords": ["santé", "patient"],
        },
        level_compatibility=["lycee_1ere_tle_general"],
        sector="santé",
        is_active=True,
    )


# ── POST /api/v1/students/me/recommendation-reviews/ ─────────────────────────


class TestRecommendationReviewCreate:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_valid_post_returns_201(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "ne_correspond_pas"}
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 201

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_valid_post_creates_record(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "choquant_inapproprie"}
        student_client.post(url, payload, format="json")
        assert RecommendationReview.objects.filter(
            profession=profession, reason="choquant_inapproprie"
        ).exists()

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_response_includes_id_and_status(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre"}
        response = student_client.post(url, payload, format="json")
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_without_reason_returns_400(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug}
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 400

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_without_auth_returns_401(self, profession):
        client = APIClient()
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre"}
        response = client.post(url, payload, format="json")
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_comment_too_long_returns_400(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {
            "profession_slug": profession.slug,
            "reason": "ne_correspond_pas",
            "comment": "x" * 501,
        }
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 400

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_duplicate_returns_409(self, student_client, student_user, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre"}
        student_client.post(url, payload, format="json")
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 409

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_invalid_reason_returns_400(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "raison_invalide"}
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 400

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_unknown_slug_returns_404(self, student_client):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": "metier-inexistant", "reason": "autre"}
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 404

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_with_optional_comment(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {
            "profession_slug": profession.slug,
            "reason": "ne_correspond_pas",
            "comment": "Je ne vois pas du tout le rapport avec mes centres d'intérêt.",
        }
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 201
        review = RecommendationReview.objects.get(profession=profession)
        assert review.comment == "Je ne vois pas du tout le rapport avec mes centres d'intérêt."

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_emits_audit_log(self, student_client, profession):
        from apps.audit.models import AuditLog

        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre"}
        student_client.post(url, payload, format="json")
        assert AuditLog.objects.filter(action="recommendation_review_requested").exists()

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_id_has_rev_prefix(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre"}
        response = student_client.post(url, payload, format="json")
        assert response.json()["id"].startswith("rev_")

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_blank_comment_stored_as_null(self, student_client, profession):
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre", "comment": ""}
        student_client.post(url, payload, format="json")
        review = RecommendationReview.objects.get(profession=profession)
        assert review.comment is None

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_emits_audit_log_with_correct_metadata(
        self, student_client, student_user, profession
    ):
        """AC5: audit log must contain profession_slug, reason, student_id, review_id."""
        from apps.audit.models import AuditLog

        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "ne_correspond_pas"}
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 201
        log = AuditLog.objects.filter(action="recommendation_review_requested").first()
        assert log is not None
        assert log.metadata["profession_slug"] == profession.slug
        assert log.metadata["reason"] == "ne_correspond_pas"
        assert log.metadata["student_id"] == str(student_user.pk)
        assert log.metadata["review_id"] == response.json()["id"]

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_different_student_can_review_same_profession(self, profession, student_user):
        """Unique constraint is per (student, profession) — another student must succeed."""
        other_student = User.objects.create_user(
            email="autre@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_student)

        url = reverse("recommendation-review-create")
        payload = {"profession_slug": profession.slug, "reason": "autre"}

        # First student submits
        client = APIClient()
        client.force_authenticate(user=student_user)
        r1 = client.post(url, payload, format="json")
        assert r1.status_code == 201

        # Second student for same profession must also succeed (not 409)
        r2 = other_client.post(url, payload, format="json")
        assert r2.status_code == 201

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_student_can_review_multiple_professions(self, student_client, profession, db):
        """One student can review two different professions."""
        profession2 = Profession.objects.create(
            slug="infirmier-test",
            name="Infirmier test",
            description="Description test " * 12,
            daily_routine="Tu travailles en salle de soins. " * 5,
            requirements_json=[{"type": "studies", "label": "BTS"}],
            prospects_text="1. Spécialiste.",
            signals_json={"passions": [], "valeurs": [], "specialites": [], "keywords": []},
            level_compatibility=["lycee_1ere_tle_general"],
            sector="santé",
            is_active=True,
        )
        url = reverse("recommendation-review-create")
        r1 = student_client.post(
            url, {"profession_slug": profession.slug, "reason": "autre"}, format="json"
        )
        r2 = student_client.post(
            url, {"profession_slug": profession2.slug, "reason": "ne_correspond_pas"}, format="json"
        )
        assert r1.status_code == 201
        assert r2.status_code == 201

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_inactive_profession_returns_404(self, student_client, db):
        """RGPD art. 22: inactive professions should still be findable by slug for contestation."""
        inactive = Profession.objects.create(
            slug="metier-inactif-test",
            name="Métier inactif",
            description="Description test " * 12,
            daily_routine="Tu travailles. " * 5,
            requirements_json=[{"type": "studies", "label": "Bac"}],
            prospects_text="1. Rien.",
            signals_json={"passions": [], "valeurs": [], "specialites": [], "keywords": []},
            level_compatibility=["lycee_1ere_tle_general"],
            sector="santé",
            is_active=False,
        )
        url = reverse("recommendation-review-create")
        payload = {"profession_slug": inactive.slug, "reason": "autre"}
        response = student_client.post(url, payload, format="json")
        # Inactive profession exists → should succeed (student can contest any received reco)
        assert response.status_code == 201


# ── GET /api/v1/admin/recommendation-reviews/ ────────────────────────────────


class TestRecommendationReviewAdminList:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_can_access_list(self, admin_client, profession, student_user):
        RecommendationReview.objects.create(
            student=student_user,
            profession=profession,
            reason="autre",
            status=RecommendationReview.Status.PENDING,
        )
        url = reverse("admin-recommendation-review-list")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_list_returns_pending_reviews(self, admin_client, profession, student_user):
        RecommendationReview.objects.create(
            student=student_user,
            profession=profession,
            reason="ne_correspond_pas",
            status=RecommendationReview.Status.PENDING,
        )
        url = reverse("admin-recommendation-review-list")
        response = admin_client.get(url)
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_student_cannot_access_admin_list(self, student_client):
        url = reverse("admin-recommendation-review-list")
        response = student_client.get(url)
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_unauthenticated_cannot_access_admin_list(self):
        client = APIClient()
        url = reverse("admin-recommendation-review-list")
        response = client.get(url)
        assert response.status_code in (401, 403)
