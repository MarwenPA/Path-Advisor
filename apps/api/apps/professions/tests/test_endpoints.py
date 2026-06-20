"""Tests for Profession API endpoints — Story 3.2 T4 / AC6.

Covers:
- GET /api/v1/admin/professions/      → 403 for students, 200 for path_admin
- GET /api/v1/admin/professions/{slug}/ → 403 for students, 200 for path_admin, 404 unknown
- GET /api/v1/professions/{slug}/     → 200 for students, sources_json absent, 404 unknown
- Audit log `profession_viewed` emitted on student detail
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.professions.models import Profession

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
            {"type": "quality", "label": "Empathie"},
            {"type": "quality", "label": "Rigueur"},
            {"type": "quality", "label": "Communication"},
        ],
        prospects_text="1. Infirmier spécialisé. 2. Cadre de santé. 3. Formateur.",
        signals_json={
            "passions": ["médecine", "aide"],
            "valeurs": ["utilité", "soin"],
            "specialites": ["svt"],
            "keywords": ["santé", "patient", "hôpital", "soins", "infirmier"],
        },
        level_compatibility=["lycee_1ere_tle_general", "postbac"],
        sector="santé",
        sources_json=["Onisep 2025", "validation humaine 2026-06"],
        median_salary_eur=32000,
        is_active=True,
    )


# ── Admin list endpoint ───────────────────────────────────────────────────────


class TestAdminProfessionList:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_can_access_list(self, admin_client, profession):
        url = reverse("professions:admin-list")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_list_returns_results(self, admin_client, profession):
        url = reverse("professions:admin-list")
        response = admin_client.get(url)
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_list_includes_sources_json(self, admin_client, profession):
        url = reverse("professions:admin-list")
        response = admin_client.get(url)
        results = response.json()["results"]
        assert results, "No results returned"
        assert "sources_json" in results[0]

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_student_cannot_access_admin_list(self, student_client, profession):
        url = reverse("professions:admin-list")
        response = student_client.get(url)
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_unauthenticated_cannot_access_admin_list(self, profession):
        client = APIClient()
        url = reverse("professions:admin-list")
        response = client.get(url)
        assert response.status_code in (401, 403)


# ── Admin detail endpoint ─────────────────────────────────────────────────────


class TestAdminProfessionDetail:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_can_access_detail(self, admin_client, profession):
        url = reverse("professions:admin-detail", kwargs={"slug": profession.slug})
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_detail_has_all_fields(self, admin_client, profession):
        url = reverse("professions:admin-detail", kwargs={"slug": profession.slug})
        response = admin_client.get(url)
        data = response.json()
        for field in ("id", "slug", "name", "sources_json", "rome_code", "created_at"):
            assert field in data, f"Admin detail missing field '{field}'"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_detail_unknown_slug_returns_404(self, admin_client):
        url = reverse("professions:admin-detail", kwargs={"slug": "metier-inexistant"})
        response = admin_client.get(url)
        assert response.status_code == 404

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_student_cannot_access_admin_detail(self, student_client, profession):
        url = reverse("professions:admin-detail", kwargs={"slug": profession.slug})
        response = student_client.get(url)
        assert response.status_code == 403


# ── Public student detail endpoint ───────────────────────────────────────────


class TestPublicProfessionDetail:
    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_student_can_access_public_detail(self, student_client, profession):
        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        response = student_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_public_detail_sources_json_absent(self, student_client, profession):
        """AC6: sources_json must NOT appear in the public student endpoint."""
        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        response = student_client.get(url)
        data = response.json()
        assert "sources_json" not in data, "sources_json must be absent from public endpoint"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_public_detail_rome_code_absent(self, student_client, profession):
        """AC6: rome_code must NOT appear in the public student endpoint."""
        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        response = student_client.get(url)
        data = response.json()
        assert "rome_code" not in data, "rome_code must be absent from public endpoint"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_public_detail_has_expected_fields(self, student_client, profession):
        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        response = student_client.get(url)
        data = response.json()
        for field in (
            "id",
            "slug",
            "name",
            "description",
            "daily_routine",
            "signals_json",
            "level_compatibility",
            "sector",
        ):
            assert field in data, f"Public detail missing field '{field}'"

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_public_detail_unknown_slug_returns_404(self, student_client):
        url = reverse("professions:public-detail", kwargs={"slug": "metier-inexistant"})
        response = student_client.get(url)
        assert response.status_code == 404

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_unauthenticated_cannot_access_public_detail(self, profession):
        client = APIClient()
        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        response = client.get(url)
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_admin_cannot_access_public_detail(self, admin_client, profession):
        """AC6: public endpoint requires STUDENT role specifically."""
        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        response = admin_client.get(url)
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.postgresql_only
    def test_public_detail_emits_audit_log(self, student_client, profession):
        """AC6 + Story 1.13: profession_viewed audit event is recorded."""
        from apps.audit.models import AuditLog

        url = reverse("professions:public-detail", kwargs={"slug": profession.slug})
        student_client.get(url)

        assert AuditLog.objects.filter(
            action="profession_viewed",
            subject_id=str(profession.pk),
        ).exists(), "No profession_viewed audit log entry found"
