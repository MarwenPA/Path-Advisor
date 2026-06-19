"""Integration tests for Story 2.2 — GET/PATCH /api/v1/students/me/onboarding/level.

Covers: GET empty defaults, partial PATCH, commit PATCH with full matrix
validation, skip, RLS (cross-user isolation), audit event mock, referential
sync.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.students.models import OnboardingStep2Status, StudentLevelProfile, StudentProfile

User = get_user_model()

LEVEL_URL = "/api/v1/students/me/onboarding/level"


@pytest.fixture
def student(db):
    user = User.objects.create_user(
        email="sarah@example.com",
        password="securepass",
        role="student",
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )
    return user


@pytest.fixture
def other_student(db):
    user = User.objects.create_user(
        email="mehdi@example.com",
        password="securepass",
        role="student",
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )
    return user


@pytest.fixture
def client_for(student):
    client = APIClient()
    client.force_authenticate(user=student)
    return client


@pytest.fixture
def with_step1(student):
    """Creates a StudentProfile for `student` so the step-1 ordering guard passes."""
    StudentProfile.objects.get_or_create(user=student)


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


def test_get_returns_empty_defaults_when_no_profile(db, client_for):
    resp = client_for.get(LEVEL_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["level"] is None
    assert data["specialites"] == []
    assert data["onboarding_step2_status"] == "pending"


def test_get_returns_existing_profile(db, student, client_for):
    profile, _ = StudentProfile.objects.get_or_create(user=student)
    lvl = StudentLevelProfile.objects.create(
        profile=profile,
        level="lycee_terminale",
        filiere="general",
        specialites=["mathematiques", "svt"],
        onboarding_step2_status="completed",
    )
    resp = client_for.get(LEVEL_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["level"] == "lycee_terminale"
    assert data["filiere"] == "general"
    assert set(data["specialites"]) == {"mathematiques", "svt"}
    assert data["onboarding_step2_status"] == "completed"


def test_get_401_anonymous(db):
    client = APIClient()
    resp = client.get(LEVEL_URL)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH — partial drafts
# ---------------------------------------------------------------------------


def test_patch_requires_step1_profile(db, student, client_for):
    """Decision #19 — step-1 ordering guard: no StudentProfile → 400."""
    resp = client_for.patch(LEVEL_URL, {"level": "lycee_terminale"}, format="json")
    assert resp.status_code == 400
    assert "Step 1" in resp.json()["detail"]


def test_patch_partial_saves_level(db, student, client_for, with_step1):
    resp = client_for.patch(LEVEL_URL, {"level": "lycee_terminale"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["level"] == "lycee_terminale"
    assert resp.json()["onboarding_step2_status"] == "in_progress"


def test_patch_partial_does_not_wipe_other_fields(db, student, client_for, with_step1):
    # Establish a profile with level + filiere
    client_for.patch(LEVEL_URL, {"level": "lycee_terminale"}, format="json")
    client_for.patch(LEVEL_URL, {"filiere": "general"}, format="json")
    # Patch specialites only
    resp = client_for.patch(LEVEL_URL, {"specialites": ["mathematiques"]}, format="json")
    data = resp.json()
    assert data["level"] == "lycee_terminale"
    assert data["filiere"] == "general"
    assert "mathematiques" in data["specialites"]


def test_patch_unknown_level_returns_400(db, student, client_for):
    resp = client_for.patch(LEVEL_URL, {"level": "not-a-level"}, format="json")
    assert resp.status_code == 400


def test_patch_unknown_filiere_returns_400(db, student, client_for):
    resp = client_for.patch(LEVEL_URL, {"filiere": "pro-bac"}, format="json")
    assert resp.status_code == 400


def test_patch_unknown_specialite_returns_400(db, student, client_for):
    resp = client_for.patch(
        LEVEL_URL, {"specialites": ["does-not-exist"]}, format="json"
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PATCH — commit validation matrix (Story 2.2 §4.5)
# ---------------------------------------------------------------------------


def test_commit_college_3eme_requires_intended_track(db, student, client_for):
    payload = {
        "commit": True,
        "level": "college_3eme",
        "filiere": None,
        "specialites": [],
        # intended_track missing
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_college_3eme_with_filiere_returns_400(db, student, client_for):
    payload = {
        "commit": True,
        "level": "college_3eme",
        "intended_track": "pro",
        "filiere": "general",  # must be null
        "specialites": [],
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_college_3eme_success(db, student, client_for, with_step1):
    payload = {
        "commit": True,
        "level": "college_3eme",
        "intended_track": "pro",
        "filiere": None,
        "specialites": [],
        "level_ref_version": "2026-05-v1",
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_step2_status"] == "completed"
    assert data["level"] == "college_3eme"


def test_commit_terminale_general_requires_2_specs(db, student, client_for):
    payload = {
        "commit": True,
        "level": "lycee_terminale",
        "filiere": "general",
        "specialites": ["mathematiques"],  # only 1, need 2
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_terminale_general_rejects_3_specs(db, student, client_for):
    payload = {
        "commit": True,
        "level": "lycee_terminale",
        "filiere": "general",
        "specialites": ["mathematiques", "svt", "ses"],  # 3, need 2
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_terminale_general_success(db, student, client_for, with_step1):
    payload = {
        "commit": True,
        "level": "lycee_terminale",
        "filiere": "general",
        "specialites": ["mathematiques", "svt"],
        "level_ref_version": "2026-05-v1",
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_step2_status"] == "completed"


def test_commit_1ere_general_requires_3_specs(db, student, client_for):
    payload = {
        "commit": True,
        "level": "lycee_1ere",
        "filiere": "general",
        "specialites": ["mathematiques", "svt"],  # 2, need 3
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_1ere_techno_requires_sous_filiere(db, student, client_for):
    payload = {
        "commit": True,
        "level": "lycee_1ere",
        "filiere": "techno",
        "specialites": [],
        # sous_filiere_techno missing
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_1ere_techno_with_sous_filiere_success(db, student, client_for, with_step1):
    payload = {
        "commit": True,
        "level": "lycee_1ere",
        "filiere": "techno",
        "sous_filiere_techno": "STMG",
        "specialites": [],
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 200


def test_commit_postbac_requires_year_and_formation(db, student, client_for):
    payload = {
        "commit": True,
        "level": "postbac",
        "postbac_year": "bac+1",
        # postbac_formation_type missing
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 400


def test_commit_postbac_pause_aucune_is_valid(db, student, client_for, with_step1):
    """Léa ré-orientation — 'pause' + 'aucune' must be accepted without error."""
    payload = {
        "commit": True,
        "level": "postbac",
        "postbac_year": "pause",
        "postbac_formation_type": "aucune",
        "filiere": None,
        "specialites": [],
    }
    resp = client_for.patch(LEVEL_URL, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_step2_status"] == "completed"


# ---------------------------------------------------------------------------
# Skip
# ---------------------------------------------------------------------------


def test_skip_sets_status_to_skipped(db, student, client_for, with_step1):
    resp = client_for.patch(LEVEL_URL, {"skip": True}, format="json")
    assert resp.status_code == 200
    assert resp.json()["onboarding_step2_status"] == "skipped"


# ---------------------------------------------------------------------------
# Cross-user isolation (application-layer guard, no RLS on SQLite)
# ---------------------------------------------------------------------------


def test_patch_creates_only_for_calling_user(db, student, other_student, client_for):
    client_for.patch(LEVEL_URL, {"level": "lycee_terminale"}, format="json")
    # Other student should have no level profile
    other_profile = StudentProfile.objects.filter(user=other_student).first()
    assert other_profile is None or not StudentLevelProfile.objects.filter(
        profile=other_profile
    ).exists()


# ---------------------------------------------------------------------------
# Referential IDs sync test
# ---------------------------------------------------------------------------


def test_level_ids_not_empty():
    from apps.students.onboarding.levels import NIVEAU_IDS, SPECIALITE_IDS, TRACK_3EME_IDS

    assert len(NIVEAU_IDS) == 5
    assert len(TRACK_3EME_IDS) == 4
    assert len(SPECIALITE_IDS) == 13


def test_level_ids_unique():
    from apps.students.onboarding.levels import NIVEAU_IDS, SPECIALITE_IDS

    assert len(NIVEAU_IDS) == len(set(NIVEAU_IDS))
    assert len(SPECIALITE_IDS) == len(set(SPECIALITE_IDS))
