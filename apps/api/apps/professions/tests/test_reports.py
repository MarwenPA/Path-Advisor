"""Tests for ProfessionReport API — Story 3.8.

Covers AC4, AC5, AC9 backend:
- POST /api/v1/professions/{slug}/reports/ → 201 + ProfessionReport created + audit log
- POST without error_type → 400
- POST without auth → 401
- POST with comment > 500 chars → 400
- GET /api/v1/admin/professions/reports/ → 200 for admin, 403 for student
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.professions.models import Profession, ProfessionReport

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
        slug="infirmier-test",
        name="Infirmier·ère test",
        description="Description test " * 12,
        daily_routine="Tu commences ta matinée en réalisant les soins. " * 5,
        requirements_json=[
            {"type": "studies", "label": "DEI 3 ans"},
            {"type": "skill", "label": "Soins infirmiers"},
        ],
        prospects_text="1. Infirmier spécialisé. 2. Cadre de santé. 3. Formateur.",
        signals_json={
            "passions": ["médecine"],
            "valeurs": ["soin"],
            "specialites": ["svt"],
            "keywords": ["santé"],
        },
        level_compatibility=["lycee_1ere_tle_general"],
        sector="santé",
        is_active=True,
    )


# ── POST /api/v1/professions/{slug}/reports/ ─────────────────────────────────


class TestProfessionReportCreate:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_valid_post_returns_201(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        response = student_client.post(url, {"error_type": "description_inexacte"}, format="json")
        assert response.status_code == 201

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_valid_post_creates_record(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        student_client.post(url, {"error_type": "lien_casse"}, format="json")
        assert ProfessionReport.objects.filter(
            profession=profession, error_type="lien_casse"
        ).exists()

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_response_includes_id_and_status(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        response = student_client.post(url, {"error_type": "autre"}, format="json")
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_without_error_type_returns_400(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        response = student_client.post(url, {}, format="json")
        assert response.status_code == 400

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_without_auth_returns_401(self, profession):
        client = APIClient()
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        response = client.post(url, {"error_type": "autre"}, format="json")
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_comment_too_long_returns_400(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        payload = {"error_type": "description_inexacte", "comment": "x" * 501}
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 400

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_with_optional_fields(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        payload = {
            "error_type": "debouches_perimes",
            "location": "section Infos pratiques",
            "comment": "Le salaire est incorrect.",
        }
        response = student_client.post(url, payload, format="json")
        assert response.status_code == 201
        report = ProfessionReport.objects.get(profession=profession)
        assert report.location == "section Infos pratiques"
        assert report.comment == "Le salaire est incorrect."

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_emits_audit_log(self, student_client, profession):
        from apps.audit.models import AuditLog

        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        student_client.post(url, {"error_type": "autre"}, format="json")

        assert AuditLog.objects.filter(action="profession_report_created").exists()

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_unknown_slug_returns_404(self, student_client):
        url = reverse("professions:report-create", kwargs={"slug": "metier-inexistant"})
        response = student_client.post(url, {"error_type": "autre"}, format="json")
        assert response.status_code == 404

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_post_invalid_error_type_returns_400(self, student_client, profession):
        url = reverse("professions:report-create", kwargs={"slug": profession.slug})
        response = student_client.post(url, {"error_type": "type_invalide"}, format="json")
        assert response.status_code == 400


# ── GET /api/v1/admin/professions/reports/ ───────────────────────────────────


class TestProfessionReportAdminList:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_can_access_list(self, admin_client, profession, student_user):
        ProfessionReport.objects.create(
            profession=profession,
            reporter=student_user,
            error_type="autre",
            status="pending",
        )
        url = reverse("professions:admin-reports-list")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_list_returns_pending_reports(self, admin_client, profession, student_user):
        ProfessionReport.objects.create(
            profession=profession,
            reporter=student_user,
            error_type="lien_casse",
            status="pending",
        )
        url = reverse("professions:admin-reports-list")
        response = admin_client.get(url)
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_student_cannot_access_admin_reports(self, student_client):
        url = reverse("professions:admin-reports-list")
        response = student_client.get(url)
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_unauthenticated_cannot_access_admin_reports(self):
        client = APIClient()
        url = reverse("professions:admin-reports-list")
        response = client.get(url)
        assert response.status_code in (401, 403)
