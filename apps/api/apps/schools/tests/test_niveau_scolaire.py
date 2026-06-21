"""Tests for Story 4.7 — Adaptation graphe par niveau scolaire.

Covers:
  - ParcoursListView ?niveau_scolaire= filtering
  - Fallback to terminale_generale when no exact match (AC4)
  - Fallback to all when no terminale_generale either
  - is_default=True sorted first
  - Seed has >= 4 bac pro parcours (AC6)
"""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.professions.models import Profession
from apps.schools.models import Parcours, School

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_profession(slug: str, name: str | None = None) -> Profession:
    return Profession.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name or slug,
            "description": "Test profession description for parcours testing.",
            "daily_routine": "Tu réalises des tâches quotidiennes liées à ce métier.",
            "requirements_json": [{"type": "skill", "label": "Compétence test"}],
            "prospects_text": "Évolution possible vers des postes d'encadrement.",
            "signals_json": {"passions": [], "keywords": [slug]},
            "level_compatibility": ["lycee_1ere_tle_pro", "college_3eme"],
        },
    )[0]


def _make_student() -> User:
    from django.db import connection

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', 'true', true)")
    user = User.objects.create_user(
        email=f"student-{User.objects.count()}@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', '', true)")
    return user


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def student_user(db):
    return _make_student()


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def profession_aero(db):
    return _make_profession("technicien-aeronautique-test", "Technicien aéronautique test")


@pytest.fixture
def profession_cuisine(db):
    return _make_profession("cuisinier-test", "Cuisinier test")


@pytest.fixture
def school(db):
    return School.objects.create(
        slug="test-school-parcours",
        name="École Test Parcours",
        type=School.Type.LYCEE_PRO,
        city="Paris",
        region="Île-de-France",
        postal_code="75001",
        selectivity_index=5,
        public_private=School.PublicPrivate.PUBLIC,
    )


# ── T1 — bac pro parcours returned for troisieme_bac_pro ─────────────────────


@pytest.mark.django_db
def test_bac_pro_parcours_returned_for_troisieme(student_client, profession_aero, school):
    """?niveau_scolaire=troisieme_bac_pro returns bac pro parcours."""
    Parcours.objects.create(
        profession=profession_aero,
        target_school=school,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
        is_default=True,
        nodes=[],
        edges=[],
    )
    bac_pro = Parcours.objects.create(
        profession=profession_aero,
        target_school=None,
        niveau_scolaire=Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        is_default=True,
        nodes=[{"id": "start", "label": "3ème", "type": "start"}],
        edges=[],
    )

    url = reverse("schools:metier-parcours-list", kwargs={"slug": profession_aero.slug})
    response = student_client.get(url, {"niveau_scolaire": "troisieme_bac_pro"})
    assert response.status_code == 200

    data = response.json()
    # Only the bac pro parcours should be returned
    ids = [item["id"] for item in data]
    assert str(bac_pro.id) in ids
    assert all(item["niveau_scolaire"] == "troisieme_bac_pro" for item in data)


# ── T2 — fallback to terminale_generale ──────────────────────────────────────


@pytest.mark.django_db
def test_fallback_to_terminale_generale(student_client, profession_aero, school):
    """?niveau_scolaire=terminale_technologique falls back when no match."""
    terminale = Parcours.objects.create(
        profession=profession_aero,
        target_school=school,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
        is_default=True,
        nodes=[{"id": "start", "label": "Terminale", "type": "start"}],
        edges=[],
    )

    url = reverse("schools:metier-parcours-list", kwargs={"slug": profession_aero.slug})
    response = student_client.get(url, {"niveau_scolaire": "terminale_technologique"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1
    ids = [item["id"] for item in data]
    assert str(terminale.id) in ids
    # All returned items should be terminale_generale (the fallback)
    assert all(item["niveau_scolaire"] == "terminale_generale" for item in data)


# ── T3 — fallback returns all when no terminale_generale ─────────────────────


@pytest.mark.django_db
def test_fallback_returns_all_when_no_terminale(student_client, profession_aero, school):
    """If no terminale_generale exists, returns all parcours for the profession."""
    bac_pro = Parcours.objects.create(
        profession=profession_aero,
        target_school=None,
        niveau_scolaire=Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        is_default=True,
        nodes=[],
        edges=[],
    )
    terminale_pro = Parcours.objects.create(
        profession=profession_aero,
        target_school=school,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_PRO,
        is_default=False,
        nodes=[],
        edges=[],
    )

    url = reverse("schools:metier-parcours-list", kwargs={"slug": profession_aero.slug})
    response = student_client.get(url, {"niveau_scolaire": "terminale_technologique"})
    assert response.status_code == 200

    data = response.json()
    ids = [item["id"] for item in data]
    assert str(bac_pro.id) in ids
    assert str(terminale_pro.id) in ids


# ── T4 — is_default sorted first ─────────────────────────────────────────────


@pytest.mark.django_db
def test_is_default_sorted_first(student_client, profession_aero, school):
    """is_default=True comes first in the result list."""
    Parcours.objects.create(
        profession=profession_aero,
        target_school=None,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
        is_default=False,
        nodes=[],
        edges=[],
    )
    default = Parcours.objects.create(
        profession=profession_aero,
        target_school=school,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
        is_default=True,
        nodes=[],
        edges=[],
    )

    url = reverse("schools:metier-parcours-list", kwargs={"slug": profession_aero.slug})
    response = student_client.get(url, {"niveau_scolaire": "terminale_generale"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 2
    # The first item must be the default
    assert data[0]["id"] == str(default.id)
    assert data[0]["is_default"] is True


# ── T5 — seed has >= 4 bac pro parcours ──────────────────────────────────────


@pytest.mark.django_db
def test_seed_has_4_plus_bac_pro_parcours(db):
    """After seed command, Parcours.objects.filter(niveau_scolaire='troisieme_bac_pro').count() >= 4."""
    call_command("seed_schools", verbosity=0)
    count = Parcours.objects.filter(
        niveau_scolaire=Parcours.NiveauScolaire.TROISIEME_BAC_PRO
    ).count()
    assert count >= 4, f"Expected >= 4 bac pro parcours in seed, got {count}"


# ── T6 — seed is idempotent ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_seed_idempotent(db):
    """Running seed_schools twice doesn't create duplicate parcours."""
    call_command("seed_schools", verbosity=0)
    count_after_first = Parcours.objects.count()
    call_command("seed_schools", verbosity=0)
    count_after_second = Parcours.objects.count()
    assert count_after_first == count_after_second, (
        f"Seed not idempotent: {count_after_first} → {count_after_second} parcours"
    )


# ── T7 — unknown profession slug returns empty list ──────────────────────────


@pytest.mark.django_db
def test_unknown_profession_returns_empty(student_client):
    """Unknown slug returns 200 with empty list (not 404)."""
    url = reverse("schools:metier-parcours-list", kwargs={"slug": "profession-inconnue"})
    response = student_client.get(url)
    assert response.status_code == 200
    assert response.json() == []


# ── T8 — no niveau_scolaire param returns all sorted ─────────────────────────


@pytest.mark.django_db
def test_no_niveau_param_returns_all(student_client, profession_aero, school):
    """Without ?niveau_scolaire=, all parcours are returned ordered by is_default."""
    p1 = Parcours.objects.create(
        profession=profession_aero,
        target_school=school,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
        is_default=True,
        nodes=[],
        edges=[],
    )
    p2 = Parcours.objects.create(
        profession=profession_aero,
        target_school=None,
        niveau_scolaire=Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
        is_default=True,
        nodes=[],
        edges=[],
    )

    url = reverse("schools:metier-parcours-list", kwargs={"slug": profession_aero.slug})
    response = student_client.get(url)
    assert response.status_code == 200

    data = response.json()
    ids = [item["id"] for item in data]
    assert str(p1.id) in ids
    assert str(p2.id) in ids
