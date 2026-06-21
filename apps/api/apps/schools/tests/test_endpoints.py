"""Tests for Schools & Formations API endpoints — Story 4.1.

Covers:
- GET /api/v1/admin/schools/        → 403 for students, 200 for path_admin
- GET /api/v1/admin/schools/{id}/   → 403 for students, 200 for path_admin, 404 unknown
- GET /api/v1/admin/formations/     → 403 for students, 200 for path_admin
- GET /api/v1/schools/{slug}/       → 200 for authenticated, 401/403 for anonymous
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.schools.models import Formation, School

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
def school(db):
    return School.objects.create(
        slug="test-ecole-polytechnique",
        name="École Polytechnique Test",
        type=School.Type.ECOLE_INGENIEUR,
        city="Palaiseau",
        region="Île-de-France",
        postal_code="91120",
        selectivity_index=1,
        public_private=School.PublicPrivate.PUBLIC,
        description="Grande école d'ingénieurs test.",
        top_debouches=["Ingénieur", "Chercheur"],
        official_url="https://test.polytechnique.edu",
    )


@pytest.fixture
def formation(school):
    return Formation.objects.create(
        school=school,
        name="Cycle ingénieur test",
        duration_years=3,
        parcoursup_open=False,
        affelnet_open=False,
    )


# ── Admin schools list endpoint ───────────────────────────────────────────────


class TestAdminSchoolList:
    @pytest.mark.django_db
    def test_admin_can_access_list(self, admin_client, school):
        url = reverse("schools:admin-school-list")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_list_returns_results(self, admin_client, school):
        url = reverse("schools:admin-school-list")
        response = admin_client.get(url)
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    @pytest.mark.django_db
    def test_admin_list_has_expected_fields(self, admin_client, school):
        url = reverse("schools:admin-school-list")
        response = admin_client.get(url)
        results = response.json()["results"]
        assert results, "No results returned"
        for field in ("id", "slug", "name", "type", "city", "region"):
            assert field in results[0], f"Admin list missing field '{field}'"

    @pytest.mark.django_db
    def test_student_cannot_access_admin_list(self, student_client, school):
        url = reverse("schools:admin-school-list")
        response = student_client.get(url)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_cannot_access_admin_list(self, school):
        client = APIClient()
        url = reverse("schools:admin-school-list")
        response = client.get(url)
        assert response.status_code in (401, 403)


# ── Admin schools detail endpoint ─────────────────────────────────────────────


class TestAdminSchoolDetail:
    @pytest.mark.django_db
    def test_admin_can_access_detail(self, admin_client, school):
        url = reverse("schools:admin-school-detail", kwargs={"pk": school.pk})
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_detail_has_all_fields(self, admin_client, school):
        url = reverse("schools:admin-school-detail", kwargs={"pk": school.pk})
        response = admin_client.get(url)
        data = response.json()
        for field in (
            "id",
            "slug",
            "name",
            "type",
            "city",
            "region",
            "postal_code",
            "selectivity_index",
            "public_private",
            "formations",
            "created_at",
            "updated_at",
        ):
            assert field in data, f"Admin detail missing field '{field}'"

    @pytest.mark.django_db
    def test_admin_detail_includes_formations(self, admin_client, school, formation):
        url = reverse("schools:admin-school-detail", kwargs={"pk": school.pk})
        response = admin_client.get(url)
        data = response.json()
        assert isinstance(data["formations"], list)
        assert len(data["formations"]) == 1
        assert data["formations"][0]["name"] == formation.name

    @pytest.mark.django_db
    def test_admin_detail_unknown_id_returns_404(self, admin_client):
        import uuid

        url = reverse("schools:admin-school-detail", kwargs={"pk": str(uuid.uuid4())})
        response = admin_client.get(url)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_student_cannot_access_admin_detail(self, student_client, school):
        url = reverse("schools:admin-school-detail", kwargs={"pk": school.pk})
        response = student_client.get(url)
        assert response.status_code == 403


# ── Admin formations list endpoint ────────────────────────────────────────────


class TestAdminFormationList:
    @pytest.mark.django_db
    def test_admin_can_access_formations_list(self, admin_client, formation):
        url = reverse("schools:admin-formation-list")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_formations_list_returns_results(self, admin_client, formation):
        url = reverse("schools:admin-formation-list")
        response = admin_client.get(url)
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    @pytest.mark.django_db
    def test_admin_formations_includes_school_nested(self, admin_client, formation):
        url = reverse("schools:admin-formation-list")
        response = admin_client.get(url)
        results = response.json()["results"]
        assert results
        assert "school" in results[0]
        assert results[0]["school"]["slug"] == formation.school.slug

    @pytest.mark.django_db
    def test_student_cannot_access_formations_list(self, student_client, formation):
        url = reverse("schools:admin-formation-list")
        response = student_client.get(url)
        assert response.status_code == 403


# ── Public school detail endpoint ─────────────────────────────────────────────


class TestPublicSchoolDetail:
    @pytest.mark.django_db
    def test_student_can_access_public_detail(self, student_client, school):
        url = reverse("schools:school-detail", kwargs={"slug": school.slug})
        response = student_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_can_access_public_detail(self, admin_client, school):
        """Any authenticated user can access the public school detail."""
        url = reverse("schools:school-detail", kwargs={"slug": school.slug})
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_public_detail_has_expected_fields(self, student_client, school):
        url = reverse("schools:school-detail", kwargs={"slug": school.slug})
        response = student_client.get(url)
        data = response.json()
        for field in (
            "id",
            "slug",
            "name",
            "type",
            "city",
            "region",
            "postal_code",
            "selectivity_index",
            "public_private",
            "top_debouches",
            "formations",
            "official_url",
        ):
            assert field in data, f"Public detail missing field '{field}'"

    @pytest.mark.django_db
    def test_public_detail_includes_formations(self, student_client, school, formation):
        url = reverse("schools:school-detail", kwargs={"slug": school.slug})
        response = student_client.get(url)
        data = response.json()
        assert isinstance(data["formations"], list)
        assert len(data["formations"]) == 1

    @pytest.mark.django_db
    def test_public_detail_unknown_slug_returns_404(self, student_client):
        url = reverse("schools:school-detail", kwargs={"slug": "ecole-inexistante"})
        response = student_client.get(url)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_unauthenticated_cannot_access_public_detail(self, school):
        client = APIClient()
        url = reverse("schools:school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        assert response.status_code in (401, 403)
