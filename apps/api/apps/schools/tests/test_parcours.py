"""Tests for the Parcours model and API endpoint — Story 4.3 T5.

All tests are marked @pytest.mark.postgresql_only because the project uses
django.contrib.postgres.fields.ArrayField in the professions migration which
requires PostgreSQL. Run with:
    cd apps/api && uv run pytest apps/schools/tests/test_parcours.py -v \\
        --django-settings=path_advisor.settings.test_postgres
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.professions.models import Profession
from apps.schools.models import Parcours, School

# ── helpers ────────────────────────────────────────────────────────────────────

NODES_SAMPLE = [
    {"id": "start", "label": "Terminale", "type": "start"},
    {"id": "target", "label": "IFSI Paris", "type": "target", "schoolSlug": "ifsi-paris"},
]

EDGES_SAMPLE = [
    {"source": "start", "target": "target", "weight": 2},
]


def _make_user(email: str, role: UserRole = UserRole.STUDENT) -> User:
    return User.objects.create_user(
        email=email,
        password="Strong1!pass",
        role=role,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


def _make_profession(slug: str = "infirmier-test") -> Profession:
    return Profession.objects.create(
        slug=slug,
        name="Infirmier·ère test",
        description="Description test " * 12,
        daily_routine="Tu commences ta matinée. " * 5,
        requirements_json=[
            {"type": "studies", "label": "DEI"},
            {"type": "skill", "label": "Soins"},
            {"type": "quality", "label": "Empathie"},
            {"type": "quality", "label": "Rigueur"},
            {"type": "quality", "label": "Communication"},
        ],
        prospects_text="1. Infirmier spécialisé. 2. Cadre de santé. 3. Formateur.",
        signals_json={
            "passions": ["médecine"],
            "valeurs": ["soin"],
            "specialites": ["svt"],
            "keywords": [],
        },
        level_compatibility=["lycee_1ere_tle_general"],
        sector="santé",
    )


def _make_school(slug: str = "ifsi-paris") -> School:
    return School.objects.create(
        slug=slug,
        name="IFSI Paris",
        city="Paris",
        school_type="IFSI",
    )


# ── fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def student_user(db):
    return _make_user("eleve@test.local")


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def profession(db):
    return _make_profession()


@pytest.fixture
def school(db):
    return _make_school()


@pytest.fixture
def parcours(db, profession, school):
    return Parcours.objects.create(
        profession=profession,
        target_school=school,
        nodes=NODES_SAMPLE,
        edges=EDGES_SAMPLE,
        niveau_scolaire="lycee_1ere_tle_general",
        is_default=True,
    )


# ── model tests ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_parcours_creation(profession, school):
    """Parcours can be created, saved, and retrieved with correct fields."""
    p = Parcours.objects.create(
        profession=profession,
        target_school=school,
        nodes=NODES_SAMPLE,
        edges=EDGES_SAMPLE,
        niveau_scolaire="terminale",
        is_default=True,
    )
    retrieved = Parcours.objects.get(pk=p.pk)
    assert retrieved.profession_id == profession.pk
    assert retrieved.target_school_id == school.pk
    assert retrieved.nodes == NODES_SAMPLE
    assert retrieved.edges == EDGES_SAMPLE
    assert retrieved.niveau_scolaire == "terminale"
    assert retrieved.is_default is True


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_school_creation():
    """School can be created and str representation works."""
    school = School.objects.create(slug="test-school", name="Test School", city="Paris")
    assert str(school) == "Test School (Paris)"


# ── API tests ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_returns_parcours_for_profession(student_client, parcours, profession):
    """GET /api/v1/metiers/{slug}/parcours/ returns 200 with a list containing the parcours."""
    url = f"/api/v1/metiers/{profession.slug}/parcours/"
    response = student_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert str(data[0]["id"]) == str(parcours.id)
    assert data[0]["target_school_name"] == parcours.target_school.name
    assert data[0]["target_school_slug"] == parcours.target_school.slug
    assert data[0]["nodes"] == NODES_SAMPLE


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_filters_by_niveau_scolaire(student_client, profession, school):
    """?niveau_scolaire= query param filters results to matching niveau only."""
    Parcours.objects.create(
        profession=profession,
        target_school=school,
        nodes=NODES_SAMPLE,
        edges=EDGES_SAMPLE,
        niveau_scolaire="terminale",
        is_default=True,
    )
    # Create a second school+parcours for different niveau
    school2 = School.objects.create(slug="school-two", name="School Two", city="Lyon")
    Parcours.objects.create(
        profession=profession,
        target_school=school2,
        nodes=NODES_SAMPLE,
        edges=EDGES_SAMPLE,
        niveau_scolaire="college_3eme",
        is_default=True,
    )
    url = f"/api/v1/metiers/{profession.slug}/parcours/?niveau_scolaire=terminale"
    response = student_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["niveau_scolaire"] == "terminale"


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_empty_for_unknown_profession(student_client):
    """GET for an unknown profession slug returns 200 with an empty list (not 404)."""
    url = "/api/v1/metiers/does-not-exist/parcours/"
    response = student_client.get(url)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_empty_for_profession_without_parcours(student_client, profession):
    """GET for a profession with no parcours returns 200 empty list."""
    url = f"/api/v1/metiers/{profession.slug}/parcours/"
    response = student_client.get(url)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_401_unauthenticated(parcours, profession):
    """Unauthenticated requests return 401."""
    client = APIClient()
    url = f"/api/v1/metiers/{profession.slug}/parcours/"
    response = client.get(url)
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_default_parcours_ordered_first(student_client, profession, school):
    """is_default=True parcours comes first in the response list."""
    school2 = School.objects.create(slug="school-alt", name="Ecole Alternative", city="Lyon")
    Parcours.objects.create(
        profession=profession,
        target_school=school2,
        nodes=NODES_SAMPLE,
        edges=[],
        niveau_scolaire="terminale",
        is_default=False,
    )
    default_p = Parcours.objects.create(
        profession=profession,
        target_school=school,
        nodes=NODES_SAMPLE,
        edges=EDGES_SAMPLE,
        niveau_scolaire="terminale",
        is_default=True,
    )
    url = f"/api/v1/metiers/{profession.slug}/parcours/"
    response = student_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert str(data[0]["id"]) == str(default_p.id)
