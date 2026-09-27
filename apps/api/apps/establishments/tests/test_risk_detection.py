"""Story 10.1 — profils à risque : règles de détection, frontière de
consentement, marqueur d'intervention.

Contrats clés : la règle engagement (last_login, donnée déjà exposée par le
dashboard 6.6) couvre toute la cohorte ; les règles profil/bulletins ne
courent QUE pour un consentement 6.7 accordé ; l'intervention en cours
déplace l'élève sans le faire disparaître ; l'élève n'a aucun accès.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.bulletins.models import BulletinManual
from apps.core.rls import bypass_rls
from apps.establishments.models import (
    Cohort,
    CounselorConsent,
    CounselorConsentStatus,
    CounselorIntervention,
    EstablishmentType,
    LicenseType,
    StudentImportInvitation,
    StudentImportInvitationStatus,
)
from apps.establishments.models import Establishment as EstablishmentModel
from apps.establishments.services.risk_detection import get_at_risk_students
from apps.students.models import OnboardingStep1Status, StudentLevelProfile, StudentProfile

pytestmark = pytest.mark.django_db

AT_RISK_URL = "/api/v1/establishments/cohort-dashboard/at-risk/"

_uai_counter = iter(range(5000, 6000))


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_risk_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


def _establishment() -> EstablishmentModel:
    n = next(_uai_counter)
    with bypass_rls(reason="test_setup.create_establishment"):
        return EstablishmentModel.objects.create(
            name=f"Lycée Risque Test {n}",
            type=EstablishmentType.LYCEE,
            city="Paris",
            uai=f"075{n:04d}R",
            contact_name="Karim",
            contact_email=f"karim-risk{n}@ex.test",
            license_start="2026-09-01",
            license_end="2027-08-31",
            license_type=LicenseType.PILOTE_GRATUIT,
        )


def _cohort(establishment) -> Cohort:
    with bypass_rls(reason="test_setup.create_cohort"):
        return Cohort.objects.create(
            establishment=establishment,
            name="Terminale Risque",
            school_year="2025-2026",
            tenant_id=establishment.id,
            user_id="usr_test_setup",
        )


def _student(
    cohort,
    *,
    email: str,
    last_login_days_ago: int | None = 2,
    passions: list[str] | None = None,
    specialites: list[str] | None = None,
) -> User:
    student = _uf(email=email, role=UserRole.STUDENT)
    if last_login_days_ago is not None:
        student.last_login = timezone.now() - timedelta(days=last_login_days_ago)
        with bypass_rls(reason="test_setup.set_last_login"):
            student.save(update_fields=["last_login"])
    with bypass_rls(reason="test_setup.create_invitation_and_profile"):
        StudentImportInvitation.objects.create(
            cohort=cohort,
            user=student,
            token="tok_" + student.id,
            status=StudentImportInvitationStatus.ACCEPTED,
            accepted_at=timezone.now() - timedelta(days=90),
        )
        profile = StudentProfile.objects.create(
            user=student,
            onboarding_step1_status=OnboardingStep1Status.COMPLETED,
            passions=passions or [],
        )
        if specialites is not None:
            StudentLevelProfile.objects.create(
                profile=profile,
                level="lycee_terminale",
                filiere="generale",
                specialites=specialites,
            )
    return student


def _counselor(establishment, email="counselor-risk@test.local") -> User:
    counselor = _uf(email=email, role=UserRole.COUNSELOR, tenant_id=establishment.id)
    counselor.is_verified = lambda: True
    return counselor


def _grant_consent(counselor, student, cohort) -> None:
    with bypass_rls(reason="test_setup.grant_consent"):
        CounselorConsent.objects.create(
            student=student,
            counselor=counselor,
            cohort=cohort,
            status=CounselorConsentStatus.GRANTED,
            decided_at=timezone.now(),
        )


def _bulletin(student, notes: list[float], days_ago: int) -> None:
    with bypass_rls(reason="test_setup.create_bulletin"):
        b = BulletinManual.objects.create(
            student=student.student_profile,
            trimestre_label=f"T-{days_ago}",
            year="2025-2026",
            matieres=[{"subject_id": f"m{i}", "note": n} for i, n in enumerate(notes)],
        )
        BulletinManual.objects.filter(pk=b.pk).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )


def _entry(payload, student):
    return next((e for e in payload["students"] if e["student_id"] == student.id), None)


# ─── Règle engagement (sans consentement) ────────────────────────────────────


def test_inactive_student_is_flagged_with_days():
    est = _establishment()
    cohort = _cohort(est)
    inactive = _student(cohort, email="inactif@test.local", last_login_days_ago=45)
    active = _student(cohort, email="actif@test.local", last_login_days_ago=3)
    counselor = _counselor(est)

    payload = get_at_risk_students(counselor=counselor)
    entry = _entry(payload, inactive)
    assert entry is not None
    assert entry["reasons"][0]["code"] == "faible_engagement"
    assert entry["reasons"][0]["days_inactive"] >= 45
    assert _entry(payload, active) is None


def test_never_logged_in_counts_from_acceptance():
    est = _establishment()
    cohort = _cohort(est)
    ghost = _student(cohort, email="fantome@test.local", last_login_days_ago=None)
    counselor = _counselor(est)

    payload = get_at_risk_students(counselor=counselor)
    entry = _entry(payload, ghost)
    assert entry is not None and entry["reasons"][0]["code"] == "faible_engagement"


# ─── Frontière de consentement ───────────────────────────────────────────────


def test_profile_rules_require_granted_consent():
    est = _establishment()
    cohort = _cohort(est)
    student = _student(
        cohort,
        email="incoherent@test.local",
        passions=["tech-code", "jeux-video"],
        specialites=["hlp", "llca"],
    )
    counselor = _counselor(est)

    payload = get_at_risk_students(counselor=counselor)
    assert _entry(payload, student) is None  # actif + pas de consentement → rien
    assert payload["students_without_consent"] == 1

    _grant_consent(counselor, student, cohort)
    payload = get_at_risk_students(counselor=counselor)
    entry = _entry(payload, student)
    assert entry is not None
    assert entry["reasons"][0]["code"] == "profil_incoherent"
    assert payload["students_without_consent"] == 0


def test_coherent_profile_is_not_flagged():
    est = _establishment()
    cohort = _cohort(est)
    student = _student(
        cohort,
        email="coherent@test.local",
        passions=["tech-code", "sciences-nature"],
        specialites=["nsi", "svt"],
    )
    counselor = _counselor(est)
    _grant_consent(counselor, student, cohort)

    assert _entry(get_at_risk_students(counselor=counselor), student) is None


def test_grade_drop_over_two_points_is_flagged():
    est = _establishment()
    cohort = _cohort(est)
    student = _student(cohort, email="decrochage@test.local")
    counselor = _counselor(est)
    _grant_consent(counselor, student, cohort)
    _bulletin(student, [14.0, 15.0, 13.0], days_ago=120)  # moyenne 14.0
    _bulletin(student, [11.0, 12.0, 10.0], days_ago=30)  # moyenne 11.0 → -3.0

    entry = _entry(get_at_risk_students(counselor=counselor), student)
    assert entry is not None
    reason = entry["reasons"][0]
    assert reason["code"] == "baisse_moyenne"
    assert reason["drop"] == 3.0
    assert reason["from_average"] == 14.0 and reason["to_average"] == 11.0


def test_small_grade_drop_is_not_flagged():
    est = _establishment()
    cohort = _cohort(est)
    student = _student(cohort, email="stable@test.local")
    counselor = _counselor(est)
    _grant_consent(counselor, student, cohort)
    _bulletin(student, [14.0], days_ago=120)
    _bulletin(student, [12.5], days_ago=30)  # -1.5 ≤ 2.0

    assert _entry(get_at_risk_students(counselor=counselor), student) is None


# ─── Marqueur d'intervention ─────────────────────────────────────────────────


def test_intervention_marks_and_resolves_via_api():
    est = _establishment()
    cohort = _cohort(est)
    student = _student(cohort, email="intervention@test.local", last_login_days_ago=60)
    counselor = _counselor(est)
    client = APIClient()
    client.force_authenticate(user=counselor)
    url = f"/api/v1/establishments/students/{student.id}/intervention/"

    r = client.post(url)
    assert r.status_code == 201
    entry = _entry(get_at_risk_students(counselor=counselor), student)
    assert entry is not None and entry["intervention_in_progress"] is True

    r = client.delete(url)
    assert r.status_code == 204
    entry = _entry(get_at_risk_students(counselor=counselor), student)
    assert entry["intervention_in_progress"] is False

    # Re-marquage : la même ligne est rouverte (200, pas 201).
    assert client.post(url).status_code == 200
    assert CounselorIntervention.objects.filter(counselor=counselor, student=student).count() == 1


def test_intervention_refused_for_other_establishment_student():
    est = _establishment()
    other_est = _establishment()
    other_cohort = _cohort(other_est)
    outsider = _student(other_cohort, email="ailleurs@test.local")
    counselor = _counselor(est)
    client = APIClient()
    client.force_authenticate(user=counselor)

    r = client.post(f"/api/v1/establishments/students/{outsider.id}/intervention/")
    assert r.status_code in (403, 404)


# ─── Endpoint at-risk : accès + audit ────────────────────────────────────────


def test_at_risk_endpoint_returns_payload_and_audits():
    from apps.audit.models import AuditLog

    est = _establishment()
    cohort = _cohort(est)
    _student(cohort, email="audit-risk@test.local", last_login_days_ago=45)
    counselor = _counselor(est)
    client = APIClient()
    client.force_authenticate(user=counselor)

    r = client.get(AT_RISK_URL)
    assert r.status_code == 200
    body = r.json()
    assert len(body["students"]) == 1
    with bypass_rls(reason="test.read_audit"):
        assert AuditLog.objects.filter(action="establishments.at_risk_list_viewed").exists()


def test_student_cannot_access_at_risk_or_intervention():
    est = _establishment()
    cohort = _cohort(est)
    student = _student(cohort, email="curieux@test.local")
    client = APIClient()
    client.force_authenticate(user=student)

    assert client.get(AT_RISK_URL).status_code == 403
    assert (
        client.post(f"/api/v1/establishments/students/{student.id}/intervention/").status_code
        == 403
    )


def test_other_establishment_students_never_listed():
    est = _establishment()
    other_est = _establishment()
    _student(_cohort(other_est), email="autre-etab@test.local", last_login_days_ago=90)
    counselor = _counselor(est)

    assert get_at_risk_students(counselor=counselor)["students"] == []
