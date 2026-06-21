"""Tests for AdmissionPredictionService and admission-stat endpoint — Story 4.2.

Covers:
  - Anti-humiliation floor: expected_proba never < 5%
  - Spread behaviour with/without bulletins
  - Label assignment (sur/realiste/audacieux/estimation_indicative)
  - upsert_stat DB persistence and idempotency
  - GET /api/v1/schools/{slug}/admission-stat/ → 200 (authenticated) / 401 (anon)
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.schools.models import AdmissionStat, School
from apps.schools.services import AdmissionPredictionService

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _create_user_bypassing_rls(**kwargs) -> User:
    """Create a User, opening the RLS bypass GUC on PostgreSQL.

    Under the `postgresql_only` test lane the `users` table has FORCE RLS
    enabled.  A plain `create_user()` call inside a test hits the MODIFY
    policy and raises "new row violates row-level security policy". We
    temporarily set `app.bypass_rls = 'true'` so the INSERT is allowed —
    exactly the same mechanism used by the signup signal
    (`apps.core.rls.bypass_rls`), but inlined here to keep the fixture
    dependency-free and legible.
    """
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', 'true', true)")
    user = User.objects.create_user(**kwargs)
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.bypass_rls', '', true)")
    return user


@pytest.fixture
def student_user(db):
    return _create_user_bypassing_rls(
        email="eleve42@test.local",
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
        slug="test-ecole-selectif",
        name="École Très Sélective Test",
        type=School.Type.ECOLE_INGENIEUR,
        city="Paris",
        region="Île-de-France",
        postal_code="75000",
        selectivity_index=1,
        public_private=School.PublicPrivate.PUBLIC,
    )


@pytest.fixture
def school_non_selectif(db):
    return School.objects.create(
        slug="test-ecole-non-selectif",
        name="Université Ouverte Test",
        type=School.Type.UNIVERSITE,
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
        postal_code="69000",
        selectivity_index=5,
        public_private=School.PublicPrivate.PUBLIC,
    )


# ── Service unit tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_predict_floor_anti_humiliation(school):
    """Very low grade + très sélectif must never produce expected_proba < 5."""
    service = AdmissionPredictionService()
    prediction = service.predict(school, average_grade=7.0, has_bulletins=True)
    assert prediction.expected_proba >= 5, (
        f"Anti-humiliation floor violated: expected_proba={prediction.expected_proba}"
    )
    assert prediction.min_proba >= 5, f"min_proba below floor: min_proba={prediction.min_proba}"


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_predict_selectif_no_bulletins(school):
    """Without bulletins: label=estimation_indicative and spread >= 30 pp."""
    service = AdmissionPredictionService()
    prediction = service.predict(school, has_bulletins=False)
    assert prediction.label == AdmissionStat.Label.ESTIMATION_INDICATIVE
    spread = prediction.max_proba - prediction.min_proba
    assert spread >= 30, f"Expected spread >= 30 without bulletins, got {spread}"


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_predict_selectif_with_bulletins(school):
    """With bulletins and good grade: spread is narrower (15 pp each side)."""
    service = AdmissionPredictionService()
    prediction = service.predict(school, average_grade=15.0, has_bulletins=True)
    # spread should be exactly 2*15=30 or clamped to [5, 95]
    raw_spread = min(95, prediction.expected_proba + 15) - max(5, prediction.expected_proba - 15)
    assert raw_spread <= 30, f"Spread should be <= 30 with bulletins, got {raw_spread}"
    # Label should not be estimation_indicative
    assert prediction.label != AdmissionStat.Label.ESTIMATION_INDICATIVE


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_predict_non_selectif(school_non_selectif):
    """Non-selective school (index=5) should have expected_proba >= 70."""
    service = AdmissionPredictionService()
    prediction = service.predict(school_non_selectif, has_bulletins=True)
    assert prediction.expected_proba >= 70, (
        f"Non-selective school should be >= 70, got {prediction.expected_proba}"
    )
    assert prediction.label == AdmissionStat.Label.SUR


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_upsert_saves_to_db(school, student_user):
    """upsert_stat creates a single AdmissionStat row in the database."""
    service = AdmissionPredictionService()
    stat = service.upsert_stat(school=school, user=student_user)
    assert AdmissionStat.objects.filter(school=school, user=student_user).count() == 1
    assert stat.expected_proba >= 5
    assert stat.label is not None


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_upsert_idempotent(school, student_user):
    """Calling upsert_stat twice keeps exactly one row; previous_proba is tracked."""
    service = AdmissionPredictionService()
    # First call
    stat_first = service.upsert_stat(school=school, user=student_user)
    first_expected = stat_first.expected_proba

    # Second call with a different grade (triggers an update)
    service.upsert_stat(school=school, user=student_user, average_grade=14.0)

    count = AdmissionStat.objects.filter(school=school, user=student_user).count()
    assert count == 1, f"Expected 1 row after 2 upserts, got {count}"

    refreshed = AdmissionStat.objects.get(school=school, user=student_user)
    assert refreshed.previous_proba == first_expected


# ── API endpoint tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_endpoint_200(student_client, school):
    """Authenticated user gets 200 with admission stat payload."""
    url = reverse("schools:school-admission-stat", kwargs={"slug": school.slug})
    response = student_client.get(url)
    assert response.status_code == 200
    data = response.json()
    for field in ("min_proba", "expected_proba", "max_proba", "label", "context_line"):
        assert field in data, f"Missing field '{field}' in response"
    assert data["expected_proba"] >= 5


@pytest.mark.django_db
@pytest.mark.postgresql_only
def test_api_endpoint_401(school):
    """Unauthenticated request returns 401."""
    client = APIClient()
    url = reverse("schools:school-admission-stat", kwargs={"slug": school.slug})
    response = client.get(url)
    assert response.status_code == 401
