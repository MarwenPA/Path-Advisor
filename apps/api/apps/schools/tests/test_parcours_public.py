"""Anonymous SEO parcours-summary endpoint tests — Story 7.3.

Covers:
- GET /api/v1/public/metiers/{slug}/parcours/ — AC (niveau filter,
  no nodes/edges/admission_stat, feeds "quels bacs/formations" panel)
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.professions.models import Profession
from apps.schools.models import Parcours, School

pytestmark = pytest.mark.django_db


@pytest.fixture
def profession(db):
    return Profession.objects.create(
        slug="infirmier-parcours-test",
        name="Infirmier·ère test",
        description="Description test " * 12,
        daily_routine="Routine " * 10,
        prospects_text="Prospects",
        median_salary_eur=32000,
        level_compatibility=["lycee_1ere_tle_general"],
        is_active=True,
    )


@pytest.fixture
def school(db):
    return School.objects.create(
        slug="ifsi-paris-test",
        name="IFSI Paris Test",
        type=School.Type.ECOLE_SANTE,
        city="Paris",
        region="Île-de-France",
        postal_code="75000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        official_url="https://test.example",
    )


@pytest.fixture
def terminale_parcours(profession, school):
    return Parcours.objects.create(
        profession=profession,
        target_school=school,
        niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
        label="Bac général → IFSI",
        is_default=True,
    )


class TestParcoursPublicSeoList:
    def test_anonymous_can_access_parcours_summary(self, terminale_parcours, profession):
        client = APIClient()
        url = f"/api/v1/public/metiers/{profession.slug}/parcours/"
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_excludes_nodes_edges_and_admission_stat(self, terminale_parcours, profession):
        client = APIClient()
        url = f"/api/v1/public/metiers/{profession.slug}/parcours/"
        response = client.get(url)
        row = response.json()[0]
        assert "nodes" not in row
        assert "edges" not in row
        assert "admission_stat" not in row

    def test_has_expected_public_fields(self, terminale_parcours, profession, school):
        client = APIClient()
        url = f"/api/v1/public/metiers/{profession.slug}/parcours/"
        response = client.get(url)
        row = response.json()[0]
        assert row["niveau_scolaire"] == "terminale_generale"
        assert row["target_school_name"] == school.name
        assert row["target_school_slug"] == school.slug
        assert row["target_school_city"] == school.city

    def test_niveau_scolaire_filter(self, profession, school):
        Parcours.objects.create(
            profession=profession,
            target_school=school,
            niveau_scolaire=Parcours.NiveauScolaire.TROISIEME_BAC_PRO,
            label="3ème → Bac Pro",
        )
        Parcours.objects.create(
            profession=profession,
            target_school=school,
            niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
            label="Bac général",
        )
        client = APIClient()
        url = (
            f"/api/v1/public/metiers/{profession.slug}/parcours/?niveau_scolaire=troisieme_bac_pro"
        )
        response = client.get(url)
        data = response.json()
        assert len(data) == 1
        assert data[0]["niveau_scolaire"] == "troisieme_bac_pro"

    def test_no_silent_niveau_fallback(self, terminale_parcours, profession):
        """Adversarial-review fix: when the requested niveau has no rows, the
        public SEO endpoint must return an EMPTY list — never substitute
        terminale_generale rows under a niveau-specific heading (post-bac
        formations were being presented as 3ème options). The authenticated
        `ParcoursListView` keeps its Story 4.7 AC4 fallback."""
        client = APIClient()
        url = (
            f"/api/v1/public/metiers/{profession.slug}/parcours/?niveau_scolaire=troisieme_bac_pro"
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.json() == []

    def test_excludes_parcours_targeting_deactivated_school(self, profession, school):
        inactive = School.objects.create(
            slug="ecole-fermee-parcours-test",
            name="École Fermée",
            type=School.Type.ECOLE_SANTE,
            city="Paris",
            region="Île-de-France",
            postal_code="75000",
            selectivity_index=2,
            public_private=School.PublicPrivate.PUBLIC,
            official_url="https://test.example",
            is_active=False,
        )
        Parcours.objects.create(
            profession=profession,
            target_school=inactive,
            niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
            label="Bac général → école fermée",
        )
        Parcours.objects.create(
            profession=profession,
            target_school=school,
            niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE,
            label="Bac général → IFSI",
        )
        client = APIClient()
        url = f"/api/v1/public/metiers/{profession.slug}/parcours/"
        response = client.get(url)
        slugs = [row["target_school_slug"] for row in response.json()]
        assert school.slug in slugs
        assert inactive.slug not in slugs

    def test_empty_for_unknown_profession(self):
        client = APIClient()
        url = "/api/v1/public/metiers/metier-inexistant/parcours/"
        response = client.get(url)
        assert response.status_code == 200
        assert response.json() == []
