"""Tests for Story 4.5 — admission_stat inline in school detail and parcours nodes.

Covers:
  - GET /api/v1/schools/{slug}/ returns admission_stat object when row exists
  - GET /api/v1/schools/{slug}/ returns admission_stat=null when no row
  - GET /api/v1/metiers/{slug}/parcours/ nodes_with_stats populated for target nodes
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.professions.models import Profession
from apps.schools.models import AdmissionStat, Parcours, School

# ── Helpers ───────────────────────────────────────────────────────────────────


def _create_user_bypassing_rls(**kwargs) -> User:
    """Create a User, bypassing PostgreSQL RLS (mirrors test_admission.py fixture)."""
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', 'true', true)")
    user = User.objects.create_user(**kwargs)
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', '', true)")
    return user


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def student_user(db):
    return _create_user_bypassing_rls(
        email="eleve45@test.local",
        password="Strong1!pass",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def school(db):
    return School.objects.create(
        slug="ecole-test-45",
        name="École Test Story 4.5",
        type=School.Type.ECOLE_INGENIEUR,
        city="Paris",
        region="Île-de-France",
        postal_code="75000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
    )


@pytest.fixture
def admission_stat(school, student_user):
    return AdmissionStat.objects.create(
        school=school,
        user=student_user,
        min_proba=20,
        expected_proba=38,
        max_proba=60,
        label=AdmissionStat.Label.AUDACIEUX,
        context_line="Ce pari est ambitieux — c'est faisable avec du travail ciblé.",
        action_lever="Renforce tes matières les plus décisives pour ce parcours.",
    )


@pytest.fixture
def profession(db):
    return Profession.objects.create(
        slug="ingenieur-test-45",
        name="Ingénieur Test 4.5",
        description="Description test.",
        daily_routine="Tu commences ta matinée en…",
        requirements_json=[],
        prospects_text="Évolutions possibles.",
        level_compatibility=["postbac"],
    )


@pytest.fixture
def parcours_with_target(school, profession):
    return Parcours.objects.create(
        profession=profession,
        title="Parcours test vers l'école",
        nodes=[
            {"id": "n1", "label": "Terminale", "type": "start"},
            {
                "id": "n2",
                "label": "École Test Story 4.5",
                "type": "target",
                "schoolSlug": school.slug,
            },
        ],
        edges=[{"source": "n1", "target": "n2", "weight": 1}],
    )


# ── T5.1 — school detail includes admission_stat ──────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_school_detail_includes_admission_stat(student_client, school, admission_stat):
    """GET /api/v1/schools/{slug}/ returns admission_stat object when row exists."""
    url = reverse("schools:school-detail", kwargs={"slug": school.slug})
    response = student_client.get(url)
    assert response.status_code == 200, response.content
    data = response.json()
    assert "admission_stat" in data, "admission_stat key missing from school detail"
    stat = data["admission_stat"]
    assert stat is not None, "admission_stat should not be null when row exists"
    for field in ("expected_proba", "label", "context_line", "action_lever"):
        assert field in stat, f"admission_stat missing field '{field}'"
    assert stat["label"] in ("audacieux", "realiste", "sur", "estimation_indicative")
    assert stat["expected_proba"] == 38


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_school_detail_admission_stat_null_when_none(student_client, school):
    """GET /api/v1/schools/{slug}/ returns admission_stat=null when no row exists."""
    url = reverse("schools:school-detail", kwargs={"slug": school.slug})
    response = student_client.get(url)
    assert response.status_code == 200, response.content
    data = response.json()
    assert "admission_stat" in data, "admission_stat key should always be present in response"
    assert data["admission_stat"] is None, "admission_stat should be null when no row exists"


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_school_detail_falls_back_to_baseline(student_client, school):
    """When user has no personal stat but a baseline (user=None) exists, baseline is returned."""
    baseline = AdmissionStat.objects.create(
        school=school,
        user=None,  # baseline
        min_proba=30,
        expected_proba=55,
        max_proba=70,
        label=AdmissionStat.Label.REALISTE,
        context_line="Tu as de bonnes chances d'être admis·e.",
    )
    url = reverse("schools:school-detail", kwargs={"slug": school.slug})
    response = student_client.get(url)
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["admission_stat"] is not None
    assert data["admission_stat"]["expected_proba"] == baseline.expected_proba


# ── T5.2 — parcours nodes have inline stats ───────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_parcours_nodes_have_stats(
    student_client, school, admission_stat, profession, parcours_with_target
):
    """GET /api/v1/metiers/{slug}/parcours/ nodes_with_stats populated for target node."""
    url = reverse("schools:parcours-list", kwargs={"slug": profession.slug})
    response = student_client.get(url)
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    parcours_data = data[0]
    assert "nodes_with_stats" in parcours_data

    nodes = parcours_data["nodes_with_stats"]
    target_nodes = [n for n in nodes if n.get("type") == "target"]
    assert len(target_nodes) >= 1, "No target nodes found in nodes_with_stats"

    target = target_nodes[0]
    assert "admission_stat" in target, "Target node missing admission_stat key"
    assert target["admission_stat"] is not None
    assert target["admission_stat"]["expected_proba"] == 38
    assert target["admission_stat"]["label"] == "audacieux"


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_parcours_nodes_stat_null_when_no_stat(
    student_client, school, profession, parcours_with_target
):
    """Target node admission_stat is absent (not injected) when no AdmissionStat row."""
    url = reverse("schools:parcours-list", kwargs={"slug": profession.slug})
    response = student_client.get(url)
    assert response.status_code == 200, response.content
    data = response.json()
    nodes = data[0]["nodes_with_stats"]
    target = next(n for n in nodes if n.get("type") == "target")
    # When no stat row exists, admission_stat key should not be present or be None
    assert target.get("admission_stat") is None, (
        f"Expected admission_stat to be absent/null, got {target.get('admission_stat')}"
    )


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_parcours_list_unauthenticated(school, profession, parcours_with_target):
    """Unauthenticated request to parcours endpoint returns 401."""
    client = APIClient()
    url = reverse("schools:parcours-list", kwargs={"slug": profession.slug})
    response = client.get(url)
    assert response.status_code in (401, 403)
