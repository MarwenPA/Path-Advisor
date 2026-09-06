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
from apps.core.rls import bypass_rls
from apps.schools.models import Formation, School

# ── Fixtures ─────────────────────────────────────────────────────────────────
#
# Code-review fix (2026-09) — this file isn't `postgresql_only` (it runs on
# the SQLite fast lane by default) but IS also run against real Postgres in
# CI's RLS-parity job; its fixtures were never wrapped in `bypass_rls()` —
# `User.objects.create_user()` writes to the RLS-protected `users` table
# with no GUC set at fixture time. Same fix already applied to
# `apps/professions/tests/test_endpoints.py`.


@pytest.fixture
def student_user(db):
    with bypass_rls(reason="test_setup.create_schools_user"):
        return User.objects.create_user(
            email="eleve@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )


@pytest.fixture
def admin_user(db):
    with bypass_rls(reason="test_setup.create_schools_user"):
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


# ── Public school catalog (list) endpoint ─────────────────────────────────────


class TestPublicSchoolList:
    @pytest.mark.django_db
    def test_student_can_access_public_list(self, student_client, school):
        url = reverse("schools:school-list")
        response = student_client.get(url)
        assert response.status_code == 200
        assert response.data["results"][0]["slug"] == school.slug

    @pytest.mark.django_db
    def test_public_list_excludes_detail_only_fields(self, student_client, school):
        """Catalog rows must NOT carry formations/admission_stat (detail-only,
        N+1/user-specific — see SchoolCatalogSerializer docstring)."""
        url = reverse("schools:school-list")
        response = student_client.get(url)
        row = response.data["results"][0]
        assert "formations" not in row
        assert "admission_stat" not in row

    @pytest.mark.django_db
    def test_unauthenticated_cannot_access_public_list(self, school):
        client = APIClient()
        url = reverse("schools:school-list")
        response = client.get(url)
        assert response.status_code in (401, 403)


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


# ── Anonymous SEO detail endpoint — Story 7.2 ────────────────────────────────


class TestSchoolPublicSeoDetail:
    @pytest.mark.django_db
    def test_anonymous_can_access_seo_detail(self, school):
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_seo_detail_excludes_admission_stat(self, school):
        """§2 scope decision: AC2 requires "sélectivité brute (anonyme, pas
        personnalisée)" — no admission_stat field at all."""
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        assert "admission_stat" not in response.json()

    @pytest.mark.django_db
    def test_seo_detail_excludes_internal_id(self, school):
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        assert "id" not in response.json()

    @pytest.mark.django_db
    def test_seo_detail_has_expected_public_fields(self, school):
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        data = response.json()
        for field in (
            "slug",
            "name",
            "type",
            "city",
            "selectivity_index",
            "description",
            "top_debouches",
            "parcoursup_dates",
            "official_url",
            "formations",
        ):
            assert field in data, f"SEO detail missing field '{field}'"

    @pytest.mark.django_db
    def test_seo_detail_includes_formations(self, school, formation):
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        data = response.json()
        assert isinstance(data["formations"], list)
        assert len(data["formations"]) == 1

    @pytest.mark.django_db
    def test_seo_detail_unknown_slug_returns_404(self):
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": "ecole-inexistante"})
        response = client.get(url)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_seo_detail_cross_links_matching_metiers(self, school):
        from apps.professions.models import Profession

        Profession.objects.create(
            slug="ingenieur-test",
            name="Ingénieur",
            description="Desc " * 10,
            daily_routine="Routine " * 10,
            prospects_text="Prospects",
            median_salary_eur=45000,
            is_active=True,
        )
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        data = response.json()
        assert {"slug": "ingenieur-test", "name": "Ingénieur"} in data["metiers_cibles"]

    @pytest.mark.django_db
    def test_seo_detail_similar_schools_excludes_self_and_other_types(self, school):
        same_type = School.objects.create(
            slug="autre-ecole-ingenieur",
            name="Autre École Ingénieur",
            type=School.Type.ECOLE_INGENIEUR,
            city="Lyon",
            region="Auvergne-Rhône-Alpes",
            postal_code="69000",
            selectivity_index=2,
            public_private=School.PublicPrivate.PUBLIC,
            official_url="https://test.example",
        )
        School.objects.create(
            slug="ecole-bts",
            name="Une École BTS",
            type=School.Type.BTS,
            city="Paris",
            region="Île-de-France",
            postal_code="75000",
            selectivity_index=3,
            public_private=School.PublicPrivate.PUBLIC,
            official_url="https://test.example",
        )
        client = APIClient()
        url = reverse("schools:public-seo-school-detail", kwargs={"slug": school.slug})
        response = client.get(url)
        data = response.json()
        similar_slugs = {s["slug"] for s in data["similar_schools"]}
        assert similar_slugs == {same_type.slug}
