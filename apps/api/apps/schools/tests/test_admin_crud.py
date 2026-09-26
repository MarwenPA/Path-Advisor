"""Story 9.2 — back-office CRUD écoles + import CSV + jalons Parcoursup.

Mirror of the 9.1 profession suite, plus the two 9.2-specific contracts:
the CSV import (per-line validation, conflicts never overwrite, drafts
only, all-or-nothing) and the milestone date-lock once notified.
"""

from __future__ import annotations

import io
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.tests.factories import PathAdminUserFactory
from apps.core.rls_testing import as_path_admin
from apps.notifications.models import MilestoneKind, ParcoursupMilestone
from apps.schools.models import School, SchoolRevision, SchoolStatus

LIST_URL = "/api/v1/admin/schools/"
MILESTONES_URL = "/api/v1/admin/parcoursup-milestones/"


def _payload(slug: str = "lycee-maritime-92", **overrides) -> dict:
    base = {
        "slug": slug,
        "name": "Lycée maritime de Ciboure",
        "type": "lycee_pro",
        "city": "Ciboure",
        "region": "Nouvelle-Aquitaine",
        "postal_code": "64500",
        "selectivity_index": 2,
        "public_private": "public",
        "description": "x" * 30,
        "official_url": "https://lycee-maritime.example",
        "status": "published",
    }
    base.update(overrides)
    return base


@pytest.fixture
def admin(db):
    return PathAdminUserFactory(email="karim-admin-92@test.local", email_verified_at=timezone.now())


@pytest.fixture
def client(admin) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


@pytest.fixture
def student_client(db) -> APIClient:
    from apps.accounts.models import User, UserRole, UserStatus

    with as_path_admin():
        student = User.objects.create_user(
            email="eleve-92@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    c = APIClient()
    c.force_authenticate(user=student)
    return c


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_admin_school_writes_refuse_a_student(student_client):
    for method, url in [
        ("post", LIST_URL),
        ("post", f"{LIST_URL}import-csv/"),
        ("get", MILESTONES_URL),
        ("post", MILESTONES_URL),
    ]:
        response = getattr(student_client, method)(url, {}, format="json")
        assert response.status_code == 403, (method, url, response.status_code)


# ---------------------------------------------------------------------------
# CRUD mirror (create / draft invisible / revision / rollback / archive)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_edit_rollback_archive_cycle(client):
    resp = client.post(LIST_URL, _payload(), format="json")
    assert resp.status_code == 201, resp.content
    school = School.objects.get(slug="lycee-maritime-92")
    assert school.is_active is True
    first_revision = school.revisions.get()
    assert first_revision.action == SchoolRevision.Action.CREATED

    resp = client.patch(f"{LIST_URL}lycee-maritime-92/", {"city": "Bayonne"}, format="json")
    assert resp.status_code == 200
    school.refresh_from_db()
    assert school.city == "Bayonne"
    assert AuditLog.objects.filter(action="referential.school_updated").exists()

    resp = client.post(f"{LIST_URL}lycee-maritime-92/rollback/{first_revision.pk}/")
    assert resp.status_code == 200
    school.refresh_from_db()
    assert school.city == "Ciboure"  # restored
    assert [r.action for r in school.revisions.order_by("created_at")] == [
        "created",
        "updated",
        "rolled_back",
    ]

    resp = client.post(f"{LIST_URL}lycee-maritime-92/archive/")
    assert resp.status_code == 200
    school.refresh_from_db()
    assert school.status == SchoolStatus.ARCHIVED
    assert school.is_active is False
    assert School.objects.filter(slug="lycee-maritime-92").exists()  # never hard-deleted


@pytest.mark.django_db
def test_draft_school_hidden_from_public_catalog(client):
    client.post(LIST_URL, _payload("brouillon-ecole-92", status="draft"), format="json")
    school = School.objects.get(slug="brouillon-ecole-92")
    assert school.is_active is False
    # Public catalog (4.14/8.8) filters is_active — the draft never leaks.
    public = APIClient().get("/api/v1/public/schools/brouillon-ecole-92/")
    assert public.status_code in (401, 403, 404)


@pytest.mark.django_db
def test_list_filters_by_type_region_status(client):
    client.post(LIST_URL, _payload("lycee-a", type="lycee_pro", region="Bretagne"), format="json")
    client.post(
        LIST_URL,
        _payload("inge-b", name="ENSTA", type="ecole_ingenieur", region="Bretagne"),
        format="json",
    )
    client.post(
        LIST_URL,
        _payload("brouillon-c", name="Brouillon", region="Occitanie", status="draft"),
        format="json",
    )

    by_type = client.get(LIST_URL, {"type": "ecole_ingenieur"}).json()["results"]
    assert [r["slug"] for r in by_type] == ["inge-b"]
    by_region = client.get(LIST_URL, {"region": "bretagne"}).json()["results"]
    assert {r["slug"] for r in by_region} == {"lycee-a", "inge-b"}
    by_status = client.get(LIST_URL, {"status": "draft"}).json()["results"]
    assert [r["slug"] for r in by_status] == ["brouillon-c"]


# ---------------------------------------------------------------------------
# Import CSV
# ---------------------------------------------------------------------------

CSV_HEADER = "slug;name;type;city;region;postal_code;public_private;selectivity_index"


def _csv_upload(rows: list[str]):
    content = "\n".join([CSV_HEADER, *rows])
    return io.BytesIO(content.encode("utf-8"))


@pytest.mark.django_db
def test_csv_import_creates_drafts_reports_conflicts_and_errors(client):
    # An existing school → its line must be a CONFLICT, never an overwrite.
    client.post(LIST_URL, _payload("existante-92", name="Existante"), format="json")

    upload = _csv_upload(
        [
            "nouvelle-92;Nouvelle École;bts;Brest;Bretagne;29200;public;3",
            "existante-92;Version CSV;bts;Rennes;Bretagne;35000;public;2",
            ";Sans slug;bts;Brest;Bretagne;29200;public;1",
        ]
    )
    upload.name = "import.csv"
    resp = client.post(f"{LIST_URL}import-csv/", {"file": upload}, format="multipart")
    assert resp.status_code == 200, resp.content
    report = resp.json()

    assert report["created"] == ["nouvelle-92"]
    created = School.objects.get(slug="nouvelle-92")
    # Editorial gate: a mass import NEVER publishes directly.
    assert created.status == SchoolStatus.DRAFT
    assert created.revisions.get().action == SchoolRevision.Action.IMPORTED

    assert len(report["conflicts"]) == 1
    conflict = report["conflicts"][0]
    assert conflict["slug"] == "existante-92"
    assert conflict["existing"]["name"] == "Existante"
    assert conflict["incoming"]["name"] == "Version CSV"
    # The existing fiche was NOT touched.
    assert School.objects.get(slug="existante-92").city == "Ciboure"

    assert len(report["errors"]) == 1  # the slugless line
    assert AuditLog.objects.filter(action="referential.schools_csv_imported").exists()


@pytest.mark.django_db
def test_csv_import_rejects_missing_columns(client):
    upload = io.BytesIO(b"slug;name\nx;y")
    upload.name = "import.csv"
    resp = client.post(f"{LIST_URL}import-csv/", {"file": upload}, format="multipart")
    assert resp.status_code == 200
    report = resp.json()
    assert report["created"] == []
    assert "Colonnes manquantes" in str(report["errors"])


# ---------------------------------------------------------------------------
# Jalons Parcoursup (amendement 8.3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_milestone_create_edit_and_duplicate_guard(client):
    payload = {
        "kind": MilestoneKind.OUVERTURE,
        "campaign": "2027-2028",
        "date": (timezone.localdate() + timedelta(days=200)).isoformat(),
        "notify_days_before": 18,
    }
    resp = client.post(MILESTONES_URL, payload, format="json")
    assert resp.status_code == 201, resp.content
    milestone_id = resp.json()["id"]

    # Duplicate (kind, campaign) → the 8.3 dedup identity is unique.
    assert client.post(MILESTONES_URL, payload, format="json").status_code == 400

    resp = client.patch(
        f"{MILESTONES_URL}{milestone_id}/", {"notify_days_before": 21}, format="json"
    )
    assert resp.status_code == 200
    assert ParcoursupMilestone.objects.get(pk=milestone_id).notify_days_before == 21
    assert AuditLog.objects.filter(action="referential.milestone_updated").exists()


@pytest.mark.django_db
def test_notified_milestone_date_is_locked(client):
    milestone = ParcoursupMilestone.objects.create(
        kind=MilestoneKind.FERMETURE_VOEUX,
        campaign="lock-test",
        date=timezone.localdate() + timedelta(days=10),
        notify_days_before=7,
        notified_at=timezone.now(),  # the email LEFT
    )
    resp = client.patch(
        f"{MILESTONES_URL}{milestone.pk}/",
        {"date": (timezone.localdate() + timedelta(days=30)).isoformat()},
        format="json",
    )
    assert resp.status_code == 409
    milestone.refresh_from_db()
    assert (milestone.date - timezone.localdate()).days == 10  # untouched
