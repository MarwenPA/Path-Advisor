"""Story 6.2 — T6.1 / AC1 / AC2: linked parent sees professions + mes-paris + costs."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.core.rls import bypass_rls
from apps.family.models import ParentStudentLink
from apps.schools.models import FavoriteSchool, School

pytestmark = [pytest.mark.django_db, pytest.mark.postgresql_only]

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
    "niveau_adapted": False,
}


def _uf(**kwargs):
    with bypass_rls(reason="test_setup.create_family_user"):
        return UserFactory(**kwargs)


def _school(slug: str, *, tmin=1000, tmax=3000) -> School:
    with bypass_rls(reason="test_setup.create_school"):
        return School.objects.create(
            slug=slug,
            name=f"École {slug}",
            type=School.Type.BTS,
            city="Lyon",
            region="ARA",
            postal_code="69000",
            public_private=School.PublicPrivate.PUBLIC,
            tuition_min_eur=tmin,
            tuition_max_eur=tmax,
        )


def _favorite(student, school) -> None:
    with bypass_rls(reason="test_setup.create_favorite"):
        FavoriteSchool.objects.create(user=student, school=school)


def _dashboard_url(student_id: str) -> str:
    return reverse("family:parent-child-dashboard", kwargs={"student_id": student_id})


def _linked_pair():
    parent = _uf(role="parent")
    student = _uf()
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=student)
    return parent, student


@patch("apps.family.services.parent_view.compute_recommendations", return_value=_FAKE_RECOS)
def test_dashboard_returns_three_sections(_mock):
    parent, student = _linked_pair()
    s1 = _school("bts-a", tmin=1000, tmax=2000)
    s2 = _school("bts-b", tmin=500, tmax=1500)
    _favorite(student, s1)
    _favorite(student, s2)

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_dashboard_url(student.id))

    assert resp.status_code == 200
    body = resp.json()
    # Métiers explorés
    assert len(body["metiers_explores"]) == 1
    assert body["metiers_explores"][0]["slug"] == "developpeur"
    assert body["metiers_explores"][0]["score"] == 88
    # Mes paris
    assert len(body["mes_paris"]) == 2
    # Coûts estimés — sum of the two schools
    assert body["couts_estimes"]["total_min_eur"] == 1500
    assert body["couts_estimes"]["total_max_eur"] == 3500
    assert body["couts_estimes"]["count"] == 2
    assert len(body["couts_estimes"]["breakdown"]) == 2


@patch("apps.family.services.parent_view.compute_recommendations", return_value=_FAKE_RECOS)
def test_dashboard_never_exposes_bulletin_fields(_mock):
    parent, student = _linked_pair()
    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_dashboard_url(student.id))

    assert resp.status_code == 200
    serialized = resp.content.decode()
    for forbidden in (
        "bulletins_pdf_url",
        "bulletins_extracted",
        "teacher_appreciations",
        "appreciations",
    ):
        assert forbidden not in serialized


@patch(
    "apps.family.services.parent_view.compute_recommendations",
    side_effect=__import__(
        "apps.recommendations.services.ai_client", fromlist=["AIServiceUnavailableError"]
    ).AIServiceUnavailableError(detail="down"),
)
def test_dashboard_degrades_gracefully_when_ai_unavailable(_mock):
    parent, student = _linked_pair()
    school = _school("bts-c")
    _favorite(student, school)

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(_dashboard_url(student.id))

    assert resp.status_code == 200
    body = resp.json()
    assert body["metiers_explores"] == []
    # mes-paris + costs still render
    assert body["couts_estimes"]["count"] == 1


def test_children_list_returns_only_active_links():
    parent = _uf(role="parent")
    linked = _uf()
    other = _uf()  # noqa: F841 — created to prove it is NOT returned
    with bypass_rls(reason="test_setup.create_link"):
        ParentStudentLink.objects.create(parent=parent, student=linked)

    client = APIClient()
    client.force_authenticate(user=parent)
    resp = client.get(reverse("family:parent-children-collection"))

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == linked.id
