"""School reporting tests — Story 5.10.

Covers:
- GET /api/v1/ecole/reporting/            — KPIs (AC)
- GET /api/v1/ecole/reporting/export.csv/ — CSV export (AC)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls import bypass_rls
from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachResponse,
    EarlyOutreachResponseAction,
)
from apps.professions.models import Profession
from apps.schools.models import School, SchoolStaff

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_reporting_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


@pytest.fixture
def school(db) -> School:
    return School.objects.create(
        slug="ecole-reporting-test",
        name="École Reporting Test",
        type=School.Type.ECOLE_INGENIEUR,
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
        postal_code="69000",
        selectivity_index=2,
        public_private=School.PublicPrivate.PUBLIC,
        description="x" * 20,
        official_url="https://test.example",
    )


@pytest.fixture
def profession_a(db) -> Profession:
    return Profession.objects.create(
        slug="metier-reporting-a",
        name="Métier Reporting A",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )


@pytest.fixture
def profession_b(db) -> Profession:
    return Profession.objects.create(
        slug="metier-reporting-b",
        name="Métier Reporting B",
        description="x" * 20,
        daily_routine="x" * 20,
        prospects_text="x",
        is_active=True,
    )


@pytest.fixture
def school_admin(school) -> User:
    user = _uf(email="admin-reporting@test.local", role=UserRole.SCHOOL_ADMIN)
    with bypass_rls(reason="test_setup.link_school_staff"):
        SchoolStaff.objects.create(user=user, school=school)
    user.is_verified = lambda: True  # see test_school_reception.py for rationale
    return user


@pytest.fixture
def school_admin_client(school_admin) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=school_admin)
    return client


def _create_outreach(*, student, school, profession, **kwargs) -> EarlyOutreachRequest:
    with bypass_rls(reason="test_setup.create_outreach"):
        return EarlyOutreachRequest.objects.create(
            student=student, school=school, profession=profession, **kwargs
        )


class TestEcoleReportingView:
    def test_aggregates_counts_by_profession_and_action(
        self, school_admin_client, school, profession_a, profession_b
    ):
        s1 = _uf(email="eleve-r1@test.local", role=UserRole.STUDENT)
        s2 = _uf(email="eleve-r2@test.local", role=UserRole.STUDENT)
        s3 = _uf(email="eleve-r3@test.local", role=UserRole.STUDENT)

        o1 = _create_outreach(student=s1, school=school, profession=profession_a)
        with bypass_rls(reason="test_setup.create_response"):
            EarlyOutreachResponse.objects.create(
                request=o1, action=EarlyOutreachResponseAction.INTERESTED
            )
        _create_outreach(student=s2, school=school, profession=profession_a)  # no response yet
        _create_outreach(student=s3, school=school, profession=profession_b)

        response = school_admin_client.get(reverse("outreach:ecole-reporting"))

        assert response.status_code == 200, response.content
        body = response.json()
        assert body["total_this_month"] == 3
        assert body["total_this_year"] == 3

        by_profession = {row["profession_name"]: row["count"] for row in body["by_profession"]}
        assert by_profession[profession_a.name] == 2
        assert by_profession[profession_b.name] == 1

        by_action = {row["action"]: row["count"] for row in body["by_action"]}
        assert by_action["interested"] == 1
        assert by_action["no_response"] == 2

    def test_does_not_include_another_schools_requests(
        self, school_admin_client, school, profession_a
    ):
        other_school = School.objects.create(
            slug="autre-ecole-reporting-test",
            name="Autre École Reporting Test",
            type=School.Type.UNIVERSITE,
            city="Paris",
            region="Île-de-France",
            postal_code="75000",
            selectivity_index=3,
            public_private=School.PublicPrivate.PUBLIC,
            description="x" * 20,
            official_url="https://test.example",
        )
        student = _uf(email="eleve-r4@test.local", role=UserRole.STUDENT)
        _create_outreach(student=student, school=other_school, profession=profession_a)

        response = school_admin_client.get(reverse("outreach:ecole-reporting"))

        assert response.status_code == 200
        assert response.json()["total_this_year"] == 0

    def test_no_student_identity_leaks_into_the_reporting_payload(
        self, school_admin_client, school, profession_a
    ):
        student = _uf(email="eleve-r5@test.local", role=UserRole.STUDENT)
        _create_outreach(student=student, school=school, profession=profession_a)

        response = school_admin_client.get(reverse("outreach:ecole-reporting"))

        assert "eleve-r5@test.local" not in response.content.decode()

    def test_student_cannot_access_reporting(self):
        student = _uf(email="eleve-r6@test.local", role=UserRole.STUDENT)
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.get(reverse("outreach:ecole-reporting"))

        assert response.status_code == 403

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(reverse("outreach:ecole-reporting"))
        assert response.status_code == 401


class TestEcoleReportingExportView:
    def test_returns_a_csv_attachment(self, school_admin_client, school, profession_a):
        student = _uf(email="eleve-r7@test.local", role=UserRole.STUDENT)
        _create_outreach(student=student, school=school, profession=profession_a)

        response = school_admin_client.get(reverse("outreach:ecole-reporting-export"))

        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert "attachment" in response["Content-Disposition"]
        content = response.content.decode()
        assert profession_a.name in content
        assert "eleve-r7@test.local" not in content
