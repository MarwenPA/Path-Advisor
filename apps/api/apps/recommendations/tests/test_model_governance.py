"""Story 9.5 — versioning + journal art. 22.

Contracts: every scoring writes a decision with the version the ai-service
ANSWERED with (an unknown version is auto-registered flagged, never
silent); the snapshot is faithful enough to replay (profile + referential
slice); activation is exclusive and ETHICS-GATED (>10% inter-group gap →
409 without a review note); the journal prunes at 365 d; RBAC holds.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.tests.factories import PathAdminUserFactory
from apps.core.rls_testing import as_path_admin
from apps.recommendations.model_governance import (
    EthicsGateError,
    activate_model_version,
    prune_scoring_decisions,
    register_model_version,
)
from apps.recommendations.models import ModelVersion, ScoringDecision
from apps.recommendations.services.recommendation_service import compute_recommendations

VERSIONS_URL = "/api/v1/admin/model-versions/"

BIASED_METRICS = {
    "subpopulations": {
        "niveau": {"lycee_terminale": 0.72, "postbac": 0.60},  # 16.7% gap
    }
}


def _legacy_version():
    row, _ = ModelVersion.objects.get_or_create(
        version="0.3.0-statistical",
        defaults={
            "name": "Scorer statistique 3.3",
            "dataset_hash": "unversioned-legacy",
            "is_active": True,
        },
    )
    return row


@pytest.fixture
def admin(db):
    return PathAdminUserFactory(email="karim-95@test.local", email_verified_at=timezone.now())


@pytest.fixture
def client(admin) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


def _mk_student(email: str):
    from apps.accounts.models import User, UserRole, UserStatus
    from apps.students.models import StudentLevelProfile, StudentProfile

    with as_path_admin():
        user = User.objects.create_user(
            email=email,
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        profile = StudentProfile.objects.create(
            user=user, passions=["sciences"], valeurs=["autonomie"]
        )
        StudentLevelProfile.objects.create(profile=profile, level="lycee_terminale")
    return user


def _mk_profession(slug: str = "metier-95"):
    from apps.professions.models import Profession

    return Profession.objects.get_or_create(
        slug=slug,
        defaults=dict(
            name="Métier 9.5",
            description="x" * 120,
            daily_routine="x" * 90,
            prospects_text="a. b. c.",
            is_active=True,
            signals_json={"passions": ["sciences"], "valeurs": [], "specialites": []},
            level_compatibility=["lycee_terminale"],
        ),
    )[0]


def _fake_ai_response(profession_id: str, version: str = "0.3.0-statistical") -> dict:
    return {
        "student_id": "x",
        "model_version": version,
        "scored_occupations": [
            {
                "occupation_id": profession_id,
                "score": 0.61,
                "confidence_level": "medium",
                "signals_contributifs": [],
            }
        ],
        "computation_time_ms": 3,
    }


# ---------------------------------------------------------------------------
# Journal (art. 22)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_every_scoring_writes_a_replayable_decision():
    student = _mk_student("journal-95@test.local")
    profession = _mk_profession()

    with patch(
        "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
        return_value=_fake_ai_response(profession.id),
    ):
        data = compute_recommendations(student)

    assert data["model_version"] == "0.3.0-statistical"
    decision = ScoringDecision.objects.get(pk=data["decision_id"])
    assert decision.user_id == student.pk
    assert decision.model_version.version == "0.3.0-statistical"  # the seeded row
    # Faithful snapshot: profile AND the referential slice at decision time.
    assert decision.inputs_snapshot["profile"]["passions"] == ["sciences"]
    assert decision.inputs_snapshot["professions_data"][0]["occupation_id"] == profession.id
    assert decision.top_scores[0] == {
        "id": profession.id,
        "slug": profession.slug,
        "score": 0.61,
    }


@pytest.mark.django_db
def test_unknown_answered_version_is_autoregistered_flagged():
    """Config drift (ai-service answering a version the API never
    registered) is NEVER silent: placeholder row + ethics flag."""
    student = _mk_student("drift-95@test.local")
    profession = _mk_profession("metier-95-drift")

    with patch(
        "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
        return_value=_fake_ai_response(profession.id, version="0.4.0-fantome"),
    ):
        data = compute_recommendations(student)

    ghost = ModelVersion.objects.get(version="0.4.0-fantome")
    assert ghost.requires_ethics_review is True
    assert ScoringDecision.objects.get(pk=data["decision_id"]).model_version_id == ghost.pk


@pytest.mark.django_db
def test_journal_failure_never_breaks_the_recommendation():
    student = _mk_student("uxwins-95@test.local")
    profession = _mk_profession("metier-95-ux")

    with (
        patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            return_value=_fake_ai_response(profession.id),
        ),
        patch(
            "apps.recommendations.services.recommendation_service._log_scoring_decision",
            side_effect=RuntimeError("db down"),
        ),
    ):
        data = compute_recommendations(student)

    assert data["results"]  # the student still gets recommendations
    assert data["decision_id"] is None


# ---------------------------------------------------------------------------
# Governance: registration + ethics-gated activation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_registration_hashes_the_dataset_and_flags_biased_metrics(admin):
    _mk_profession("metier-95-hash")
    row = register_model_version(
        editor=admin,
        name="v4 test",
        version="0.4.0-test",
        hyperparameters={"passion_overlap": 0.5},
        evaluation_metrics=BIASED_METRICS,
    )
    assert len(row.dataset_hash) == 64  # real SHA256, not the legacy marker
    assert row.requires_ethics_review is True  # 16.7% > 10%
    assert AuditLog.objects.filter(action="ml.model_version_registered").exists()


@pytest.mark.django_db
def test_activation_is_ethics_gated_then_exclusive(admin):
    biased = register_model_version(
        editor=admin,
        name="v4",
        version="0.4.0-gate",
        hyperparameters={},
        evaluation_metrics=BIASED_METRICS,
    )
    with pytest.raises(EthicsGateError):
        activate_model_version(version_row=biased, editor=admin)

    # With a recorded review note the gate opens — and activation is exclusive.
    activate_model_version(
        version_row=biased, editor=admin, ethics_note="Écart analysé : artefact d'échantillon."
    )
    biased.refresh_from_db()
    assert biased.is_active is True
    assert biased.requires_ethics_review is False
    legacy = _legacy_version()
    assert legacy.is_active is False  # exactly one active
    assert AuditLog.objects.filter(action="ml.model_version_activated").exists()


@pytest.mark.django_db
def test_admin_api_lists_and_activates_with_gate(client, admin):
    row = register_model_version(
        editor=admin,
        name="v4 api",
        version="0.4.0-api",
        hyperparameters={},
        evaluation_metrics=BIASED_METRICS,
    )
    listing = client.get(VERSIONS_URL).json()["versions"]
    api_row = next(v for v in listing if v["version"] == "0.4.0-api")
    assert api_row["max_subpopulation_gap"] > 0.10
    assert api_row["requires_ethics_review"] is True

    resp = client.post(f"{VERSIONS_URL}{row.pk}/activate/", {}, format="json")
    assert resp.status_code == 409  # the AC's pre-deployment alert
    resp = client.post(
        f"{VERSIONS_URL}{row.pk}/activate/",
        {"ethics_note": "Revue faite, biais d'échantillonnage documenté."},
        format="json",
    )
    assert resp.status_code == 200


@pytest.mark.django_db
def test_model_versions_refuse_non_admin(db):
    from apps.accounts.models import User, UserRole, UserStatus

    with as_path_admin():
        student = User.objects.create_user(
            email="intrus-95@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    c = APIClient()
    c.force_authenticate(user=student)
    assert c.get(VERSIONS_URL).status_code == 403


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_prune_keeps_the_365_day_window():
    student = _mk_student("prune-95@test.local")
    version = _legacy_version()
    with as_path_admin():
        old = ScoringDecision.objects.create(
            user=student, model_version=version, inputs_snapshot={}, top_scores=[]
        )
        fresh = ScoringDecision.objects.create(
            user=student, model_version=version, inputs_snapshot={}, top_scores=[]
        )
    ScoringDecision.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - timedelta(days=400)
    )

    assert prune_scoring_decisions() == 1
    remaining = set(ScoringDecision.objects.values_list("pk", flat=True))
    assert remaining == {fresh.pk}
