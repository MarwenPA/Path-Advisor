"""Story 9.6 — drift/bias audit over the art. 22 journal.

Contracts: the hand-rolled KS test stays calm on identical distributions
and alerts on shifted ones (never below the sample floor); the baseline is
captured lazily on the active version; the bias gap reads niveau/filière
groups (≥30) and >10% arms the alert; the weekly task emails the admins,
writes the audit row and flags the model; RBAC holds.
"""

from __future__ import annotations

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.tests.factories import PathAdminUserFactory
from apps.core.rls_testing import as_path_admin
from apps.recommendations.ml_audit import (
    capture_baseline,
    ks_statistic,
    subpopulation_gaps,
)
from apps.recommendations.models import ModelVersion, ScoringDecision
from apps.recommendations.tasks import run_ml_audit

AUDIT_URL = "/api/v1/admin/ml-audit/"


def _mk_student(email: str, *, level: str = "lycee_terminale", filiere: str | None = "generale"):
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
        profile = StudentProfile.objects.create(user=user, passions=[], valeurs=[])
        StudentLevelProfile.objects.create(profile=profile, level=level, filiere=filiere)
    return user


def _active_version() -> ModelVersion:
    """The migration seed is TRUNCATEd by transaction=True tests — recreate
    it idempotently instead of assuming test order."""
    row, _ = ModelVersion.objects.get_or_create(
        version="0.3.0-statistical",
        defaults={"name": "Scorer statistique 3.3", "dataset_hash": "unversioned-legacy"},
    )
    if not row.is_active:
        row.is_active = True
        row.save(update_fields=["is_active"])
    return row


def _seed_decisions(user, version, scores: list[float]) -> None:
    with as_path_admin():
        ScoringDecision.objects.bulk_create(
            ScoringDecision(
                user=user,
                model_version=version,
                inputs_snapshot={},
                top_scores=[{"id": "x", "slug": "x", "score": score}],
            )
            for score in scores
        )


# ---------------------------------------------------------------------------
# KS (pure)
# ---------------------------------------------------------------------------


def test_ks_is_calm_on_identical_and_alerts_on_shifted():
    base = [i / 100 for i in range(100)]
    assert ks_statistic(base, list(base))["alert"] is False
    shifted = [min(1.0, x + 0.35) for x in base]
    verdict = ks_statistic(base, shifted)
    assert verdict["alert"] is True
    assert verdict["statistic"] > verdict["threshold"]


def test_ks_handles_massive_ties():
    """Live-proof catch: identical BIMODAL samples (massive ties) must give
    D≈0 — the naive two-pointer inflated it to ~0.5 and false-alerted."""
    bimodal = [0.85] * 40 + [0.55] * 40
    verdict = ks_statistic(bimodal, list(bimodal))
    assert verdict["statistic"] == 0.0
    assert verdict["alert"] is False


def test_ks_never_alerts_below_the_sample_floor():
    verdict = ks_statistic([0.1] * 10, [0.9] * 10)
    assert verdict == {
        "statistic": None,
        "threshold": None,
        "alert": False,
        "reason": "insufficient",
    }


# ---------------------------------------------------------------------------
# Baseline + drift + bias
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_baseline_is_captured_lazily_then_frozen():
    student = _mk_student("baseline-96@test.local")
    version = _active_version()
    _seed_decisions(student, version, [0.5 + i / 1000 for i in range(60)])

    assert capture_baseline(version) is True
    version.refresh_from_db()
    assert len(version.baseline_scores) == 60
    # Frozen: a second capture never rewrites it.
    _seed_decisions(student, version, [0.9] * 60)
    assert capture_baseline(version) is False


@pytest.mark.django_db
def test_subpopulation_gap_reads_niveau_and_filiere():
    version = _active_version()
    terminale = _mk_student("t-96@test.local", level="lycee_terminale")
    postbac = _mk_student("p-96@test.local", level="postbac")
    _seed_decisions(terminale, version, [0.80] * 40)
    _seed_decisions(postbac, version, [0.60] * 40)  # 25% relative gap

    gaps = subpopulation_gaps()
    niveau = gaps["dimensions"]["niveau"]
    assert niveau["groups"]["lycee_terminale"] == 0.8
    assert niveau["groups"]["postbac"] == 0.6
    assert gaps["alert"] is True  # 25% > 10%


@pytest.mark.django_db
def test_small_groups_never_arm_the_bias_alert():
    version = _active_version()
    a = _mk_student("small-a-96@test.local", level="lycee_terminale")
    b = _mk_student("small-b-96@test.local", level="postbac")
    _seed_decisions(a, version, [0.9] * 10)  # < 30 → ignored
    _seed_decisions(b, version, [0.1] * 10)
    assert subpopulation_gaps()["alert"] is False


# ---------------------------------------------------------------------------
# Weekly task: alert path
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_audit_task_alerts_flags_and_emails_admins(django_capture_on_commit_callbacks):
    PathAdminUserFactory(email="ops-96@test.local", email_verified_at=timezone.now())
    version = _active_version()
    terminale = _mk_student("alerte-t-96@test.local", level="lycee_terminale")
    postbac = _mk_student("alerte-p-96@test.local", level="postbac")
    _seed_decisions(terminale, version, [0.85] * 40)
    _seed_decisions(postbac, version, [0.55] * 40)

    with django_capture_on_commit_callbacks(execute=True):
        outcome = run_ml_audit()

    assert outcome["bias_alert"] is True
    version.refresh_from_db()
    assert version.requires_ethics_review is True  # flagged for review
    assert AuditLog.objects.filter(action="ml.audit_alert").exists()
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "Biais inter-groupes" in body or "BIAIS" in body
    assert "/admin/audit-ml" in body  # the proposed review workflow
    assert "rollback" in body.lower()


@pytest.mark.django_db(transaction=True)
def test_audit_task_is_silent_when_healthy(django_capture_on_commit_callbacks):
    PathAdminUserFactory(email="ops-quiet-96@test.local", email_verified_at=timezone.now())
    version = _active_version()
    student = _mk_student("calme-96@test.local")
    _seed_decisions(student, version, [0.6 + (i % 10) / 100 for i in range(80)])

    with django_capture_on_commit_callbacks(execute=True):
        outcome = run_ml_audit()

    assert outcome == {"drift_alert": False, "bias_alert": False}
    assert len(mail.outbox) == 0
    assert not AuditLog.objects.filter(action="ml.audit_alert").exists()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dashboard_payload_shape_and_rbac():
    admin = PathAdminUserFactory(email="karim-96@test.local", email_verified_at=timezone.now())
    client = APIClient()
    client.force_authenticate(user=admin)
    payload = client.get(AUDIT_URL).json()
    assert set(payload.keys()) == {"model", "monthly", "drift", "subpopulations"}
    assert payload["model"]["version"] == "0.3.0-statistical"

    student = _mk_student("intrus-96@test.local")
    intruder = APIClient()
    intruder.force_authenticate(user=student)
    assert intruder.get(AUDIT_URL).status_code == 403
