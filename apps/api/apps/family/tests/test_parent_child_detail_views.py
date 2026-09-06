"""Code review (2026-08) — dedicated parent detail views (AC2) + inactive-child
gating (Story 6.2)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.family.models import ParentStudentLink
from apps.family.services.parent_view import get_child_professions, resolve_linked_child
from apps.professions.models import Profession
from apps.schools.models import Formation, School

pytestmark = pytest.mark.django_db

_FAKE_RECOS = {
    "results": [
        {
            "id": "prof_dev",
            "slug": "developpeur",
            "name": "Développeur",
            "sector": "tech",
            "score": 88,
            "confidence_level": "high",
            "signals_contributifs": [{"id": "s1", "label": "Logique"}],
            "phrase_recopiable": "",
        }
    ],
}


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _linked_pair(*, student_status: str = UserStatus.ACTIVE):
    parent = _uf(role="parent")
    student = _uf(status=student_status)
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=student)
    return parent, student


def _profession(slug: str) -> Profession:
    with bypass_rls(reason="test_setup.create_profession"):
        return Profession.objects.create(
            slug=slug,
            name="Développeur",
            description="Un métier passionnant.",
            daily_routine="Code, revues, cafés.",
            median_salary_eur=42000,
            prospects_text="Lead dev, CTO.",
            sector="tech",
        )


def _school(slug: str) -> School:
    with bypass_rls(reason="test_setup.create_school"):
        school = School.objects.create(
            slug=slug,
            name=f"École {slug}",
            type=School.Type.BTS,
            city="Lyon",
            region="ARA",
            postal_code="69000",
            public_private=School.PublicPrivate.PUBLIC,
            tuition_min_eur=1000,
            tuition_max_eur=2000,
        )
        Formation.objects.create(
            school=school, name="BTS SIO", duration_years=2, parcoursup_open=True
        )
        return school


# --- Inactive-child gating (code review fix) --------------------------------


def test_resolve_linked_child_refuses_soft_deleted_student():
    parent, _student = _linked_pair(student_status=UserStatus.DELETED)
    from apps.family.exceptions import ParentNotLinkedToStudent

    with pytest.raises(ParentNotLinkedToStudent):
        resolve_linked_child(parent, _student.id)


def test_dashboard_403_for_soft_deleted_child():
    parent, student = _linked_pair(student_status=UserStatus.SUSPENDED)
    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(reverse("family:parent-child-dashboard", kwargs={"student_id": student.id}))
    assert resp.status_code == 403


# --- Dedicated métier detail view (AC2) -------------------------------------


@patch("apps.family.services.parent_view.compute_recommendations", return_value=_FAKE_RECOS)
def test_metier_detail_returns_full_profession_plus_score(_mock):
    parent, student = _linked_pair()
    _profession("developpeur")
    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(
        reverse(
            "family:parent-child-metier-detail",
            kwargs={"student_id": student.id, "slug": "developpeur"},
        )
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Développeur"
    assert body["description"] == "Un métier passionnant."
    assert body["score"] == 88
    assert body["confidence_level"] == "high"


def test_metier_detail_404_for_unknown_slug():
    parent, student = _linked_pair()
    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(
        reverse(
            "family:parent-child-metier-detail",
            kwargs={"student_id": student.id, "slug": "does-not-exist"},
        )
    )
    assert resp.status_code == 404


def test_metier_detail_403_for_unlinked_parent():
    other_parent = _uf(role="parent")
    _profession("developpeur")
    _parent, student = _linked_pair()
    client = APIClient()
    client.force_authenticate(user=other_parent)
    resp = client.get(
        reverse(
            "family:parent-child-metier-detail",
            kwargs={"student_id": student.id, "slug": "developpeur"},
        )
    )
    assert resp.status_code == 403


def test_metier_detail_never_exposes_bulletin_fields():
    """AC2/AC3 — no bulletin field ever leaves this view."""
    with patch(
        "apps.family.services.parent_view.compute_recommendations", return_value=_FAKE_RECOS
    ):
        parent, student = _linked_pair()
        _profession("developpeur")
        client = APIClient()
        client.force_authenticate(user=parent)
        resp = client.get(
            reverse(
                "family:parent-child-metier-detail",
                kwargs={"student_id": student.id, "slug": "developpeur"},
            )
        )
    serialized = resp.content.decode()
    for forbidden in ("bulletins_pdf_url", "bulletins_extracted", "appreciations", "moyenne"):
        assert forbidden not in serialized


# --- Dedicated école detail view (AC2) --------------------------------------


def test_ecole_detail_returns_school_and_formations():
    parent, student = _linked_pair()
    _school("bts-a")
    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(
        reverse(
            "family:parent-child-ecole-detail",
            kwargs={"student_id": student.id, "slug": "bts-a"},
        )
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "École bts-a"
    assert len(body["formations"]) == 1
    assert body["formations"][0]["name"] == "BTS SIO"
    # Story 6.3 §AC3 — no AdmissionStat row exists yet for this
    # (school, student) pair, so the field is present but null (this view
    # never triggers a recompute itself).
    assert body["admission_stat"] is None


def test_ecole_detail_exposes_admission_stat_without_action_lever():
    """Story 6.3 §AC3 — the parent sees the derived probability but never
    the action_lever (it names a subject + grade delta)."""
    from apps.schools.models import AdmissionStat

    parent, student = _linked_pair()
    school = _school("bts-b")
    with bypass_rls(reason="test_setup.create_admission_stat"):
        AdmissionStat.objects.create(
            school=school,
            user=student,
            min_proba=30,
            expected_proba=45,
            max_proba=60,
            label=AdmissionStat.Label.REALISTE,
            context_line="Tu as de bonnes chances d'être admis·e.",
            action_lever="+ 2 points en maths feraient passer à 58 %",
        )

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(
        reverse(
            "family:parent-child-ecole-detail",
            kwargs={"student_id": student.id, "slug": "bts-b"},
        )
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["admission_stat"]["expected_proba"] == 45
    assert body["admission_stat"]["label"] == "realiste"
    assert "action_lever" not in body["admission_stat"]
    assert "action_lever" not in resp.content.decode()


def test_ecole_detail_404_for_unknown_slug():
    parent, student = _linked_pair()
    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(
        reverse(
            "family:parent-child-ecole-detail",
            kwargs={"student_id": student.id, "slug": "does-not-exist"},
        )
    )
    assert resp.status_code == 404


def test_ecole_detail_403_for_unlinked_parent():
    other_parent = _uf(role="parent")
    _school("bts-a")
    _parent, student = _linked_pair()
    client = APIClient()
    client.force_authenticate(user=other_parent)
    resp = client.get(
        reverse(
            "family:parent-child-ecole-detail",
            kwargs={"student_id": student.id, "slug": "bts-a"},
        )
    )
    assert resp.status_code == 403


# --- Top-8 cap + documented deviation (code review patch) -------------------


@patch("apps.family.services.parent_view.compute_recommendations")
def test_professions_capped_at_eight(mock_reco):
    mock_reco.return_value = {
        "results": [
            {
                "id": f"prof_{i}",
                "slug": f"metier-{i}",
                "name": f"Métier {i}",
                "sector": "tech",
                "score": 50,
                "confidence_level": "low",
                "signals_contributifs": [],
                "phrase_recopiable": "",
            }
            for i in range(12)
        ]
    }
    _parent, student = _linked_pair()
    professions = get_child_professions(student)
    assert len(professions) == 8
