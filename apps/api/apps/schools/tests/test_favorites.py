"""Tests for FavoriteSchool model and favorite endpoints — Story 4.8.

Endpoints covered:
  POST   /api/v1/schools/{slug}/favorite/  — add to favorites
  DELETE /api/v1/schools/{slug}/favorite/  — remove from favorites
  GET    /api/v1/mes-paris/               — list user favorites
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.schools.models import FavoriteSchool, School

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="student_a@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="student_b@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def auth_client(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def school_alpha(db):
    return School.objects.create(
        slug="ifsi-paris",
        name="IFSI Paris",
        type=School.Type.ECOLE_SANTE,
        city="Paris",
        region="Île-de-France",
        postal_code="75001",
        selectivity_index=3,
        public_private=School.PublicPrivate.PUBLIC,
    )


@pytest.fixture
def school_beta(db):
    return School.objects.create(
        slug="bts-nantes",
        name="BTS Nantes",
        type=School.Type.BTS,
        city="Nantes",
        region="Pays de la Loire",
        postal_code="44000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PRIVE_SOUS_CONTRAT,
    )


# ── POST favorite ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
class TestPostFavorite:
    def test_favorite_school_created(self, auth_client, user_a, school_alpha):
        url = reverse("schools:school-favorite", kwargs={"slug": school_alpha.slug})
        response = auth_client.post(url)
        assert response.status_code == 201
        assert response.json() == {"favorited": True}
        assert FavoriteSchool.objects.filter(user=user_a, school=school_alpha).exists()

    def test_favorite_idempotent(self, auth_client, user_a, school_alpha):
        url = reverse("schools:school-favorite", kwargs={"slug": school_alpha.slug})
        auth_client.post(url)
        auth_client.post(url)
        assert FavoriteSchool.objects.filter(user=user_a, school=school_alpha).count() == 1

    def test_favorite_unknown_school_returns_404(self, auth_client):
        url = reverse("schools:school-favorite", kwargs={"slug": "ecole-inconnue"})
        response = auth_client.post(url)
        assert response.status_code == 404

    def test_favorite_401_unauthenticated(self, anon_client, school_alpha):
        url = reverse("schools:school-favorite", kwargs={"slug": school_alpha.slug})
        response = anon_client.post(url)
        assert response.status_code in (401, 403)


# ── DELETE favorite ───────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
class TestDeleteFavorite:
    def test_unfavorite(self, auth_client, user_a, school_alpha):
        FavoriteSchool.objects.create(user=user_a, school=school_alpha)
        url = reverse("schools:school-favorite", kwargs={"slug": school_alpha.slug})
        response = auth_client.delete(url)
        assert response.status_code == 200
        assert response.json() == {"favorited": False}
        assert not FavoriteSchool.objects.filter(user=user_a, school=school_alpha).exists()

    def test_unfavorite_nonexistent_is_silent(self, auth_client, school_alpha):
        url = reverse("schools:school-favorite", kwargs={"slug": school_alpha.slug})
        response = auth_client.delete(url)
        assert response.status_code == 200

    def test_unfavorite_does_not_affect_other_user(self, auth_client, user_b, school_alpha):
        # user_b independently favorited the same school
        FavoriteSchool.objects.create(user=user_b, school=school_alpha)
        url = reverse("schools:school-favorite", kwargs={"slug": school_alpha.slug})
        auth_client.delete(url)  # user_a removes their own (nonexistent) favorite
        assert FavoriteSchool.objects.filter(user=user_b, school=school_alpha).exists()


# ── GET mes-paris ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
class TestMesParisListView:
    def test_mes_paris_returns_favorited_schools(
        self, auth_client, user_a, school_alpha, school_beta
    ):
        FavoriteSchool.objects.create(user=user_a, school=school_alpha)
        FavoriteSchool.objects.create(user=user_a, school=school_beta)
        url = reverse("schools:mes-paris")
        response = auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        slugs = [s["slug"] for s in data]
        assert school_alpha.slug in slugs
        assert school_beta.slug in slugs

    def test_mes_paris_empty_for_new_user(self, auth_client):
        url = reverse("schools:mes-paris")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.json() == []

    def test_mes_paris_excludes_other_users_favorites(self, auth_client, user_b, school_alpha):
        FavoriteSchool.objects.create(user=user_b, school=school_alpha)
        url = reverse("schools:mes-paris")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.json() == []

    def test_mes_paris_401_unauthenticated(self, anon_client):
        url = reverse("schools:mes-paris")
        response = anon_client.get(url)
        assert response.status_code in (401, 403)

    def test_mes_paris_ordered_by_most_recent(self, auth_client, user_a, school_alpha, school_beta):
        # Create in order: alpha first, beta second — beta should come first in response
        FavoriteSchool.objects.create(user=user_a, school=school_alpha)
        FavoriteSchool.objects.create(user=user_a, school=school_beta)
        url = reverse("schools:mes-paris")
        response = auth_client.get(url)
        data = response.json()
        assert len(data) == 2
        # Most recently added (beta) should be first
        assert data[0]["slug"] == school_beta.slug

    def test_mes_paris_school_has_expected_fields(self, auth_client, user_a, school_alpha):
        FavoriteSchool.objects.create(user=user_a, school=school_alpha)
        url = reverse("schools:mes-paris")
        response = auth_client.get(url)
        school_data = response.json()[0]
        for field in ("id", "slug", "name", "type", "city", "region", "formations"):
            assert field in school_data, f"mes-paris response missing field '{field}'"
