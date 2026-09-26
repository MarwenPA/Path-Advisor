"""Story 9.1 — back-office CRUD on the professions referential.

Contracts: IsPathAdmin everywhere; `status` drives `is_active` (a draft or
an archived fiche disappears from EVERY public surface); one revision per
write; rollback restores and appends (never rewrites); every write leaves
an audit row.
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.core.rls_testing import as_path_admin
from apps.professions.models import Profession, ProfessionRevision, ProfessionStatus

LIST_URL = "/api/v1/admin/professions/"


def _payload(slug: str = "cartographe-marin", **overrides) -> dict:
    base = {
        "slug": slug,
        "name": "Cartographe marin",
        "description": "x" * 120,
        "daily_routine": "Tu commences ta matinée en " + "y" * 80,
        "requirements_json": [{"type": "studies", "label": "Licence de géographie"}],
        "prospects_text": "Hydrographe. Océanographe. Chef de mission.",
        "median_salary_eur": 32000,
        "salary_range_json": {"min": 26000, "max": 45000, "source": "Onisep 2026"},
        "signals_json": {
            "passions": ["mer", "cartes"],
            "valeurs": ["précision"],
            "specialites": [],
        },
        "level_compatibility": ["postbac"],
        "sector": "environnement",
        "sources_json": ["Onisep"],
        "status": "published",
    }
    base.update(overrides)
    return base


@pytest.fixture
def admin(db):
    # Canonical staff fixture (audit tests): superuser bypasses the
    # `requires_mfa_verified` gate the same way a real DPO break-glass
    # account does — the MFA gate itself is pinned by the 1.6/1.7 suites.
    from apps.audit.tests.factories import PathAdminUserFactory

    return PathAdminUserFactory(email="karim-admin@test.local", email_verified_at=timezone.now())


@pytest.fixture
def client(admin) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


@pytest.fixture
def student_client(db) -> APIClient:
    with as_path_admin():
        student = User.objects.create_user(
            email="eleve-91@test.local",
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
def test_every_admin_endpoint_refuses_a_student(student_client):
    prof = Profession.objects.create(**_payload("permis-91"))
    for method, url in [
        ("get", LIST_URL),
        ("post", LIST_URL),
        ("get", f"{LIST_URL}permis-91/"),
        ("patch", f"{LIST_URL}permis-91/"),
        ("post", f"{LIST_URL}permis-91/archive/"),
        ("get", f"{LIST_URL}permis-91/revisions/"),
        ("post", f"{LIST_URL}permis-91/rollback/prev_x/"),
    ]:
        response = getattr(student_client, method)(url, {}, format="json")
        assert response.status_code == 403, (method, url, response.status_code)
    assert prof.revisions.count() == 0  # nothing wrote anything


# ---------------------------------------------------------------------------
# Create / status sync
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_publishes_and_appears_in_public_catalog(client):
    resp = client.post(LIST_URL, _payload(), format="json")
    assert resp.status_code == 201, resp.content
    prof = Profession.objects.get(slug="cartographe-marin")
    assert prof.status == ProfessionStatus.PUBLISHED
    assert prof.is_active is True  # the sync — public queries keep working
    assert prof.revisions.get().action == ProfessionRevision.Action.CREATED
    assert AuditLog.objects.filter(
        action="referential.profession_created", subject_id=prof.id
    ).exists()


@pytest.mark.django_db
def test_draft_is_invisible_on_every_public_surface(client):
    resp = client.post(LIST_URL, _payload("brouillon-91", status="draft"), format="json")
    assert resp.status_code == 201
    prof = Profession.objects.get(slug="brouillon-91")
    assert prof.is_active is False
    # Public catalog (3.13) and SEO fiche (7.1) both filter is_active.
    assert APIClient().get("/api/v1/public/professions/brouillon-91/").status_code == 404
    # But the admin detail sees it.
    assert client.get(f"{LIST_URL}brouillon-91/").status_code == 200


@pytest.mark.django_db
def test_signals_json_shape_is_enforced(client):
    bad = _payload("mal-forme", signals_json={"passions": "sciences"})
    resp = client.post(LIST_URL, bad, format="json")
    assert resp.status_code == 400
    assert "passions" in str(resp.content)


# ---------------------------------------------------------------------------
# Update / revisions / audit
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_appends_a_revision_and_an_audit_row(client):
    client.post(LIST_URL, _payload(), format="json")
    resp = client.patch(
        f"{LIST_URL}cartographe-marin/", {"median_salary_eur": 35000}, format="json"
    )
    assert resp.status_code == 200
    prof = Profession.objects.get(slug="cartographe-marin")
    assert prof.median_salary_eur == 35000
    revs = list(prof.revisions.order_by("created_at"))
    assert [r.action for r in revs] == ["created", "updated"]
    row = AuditLog.objects.get(action="referential.profession_updated")
    assert row.metadata["changed_fields"] == ["median_salary_eur"]


@pytest.mark.django_db
def test_noop_patch_writes_nothing(client):
    client.post(LIST_URL, _payload(), format="json")
    client.patch(f"{LIST_URL}cartographe-marin/", {"median_salary_eur": 32000}, format="json")
    prof = Profession.objects.get(slug="cartographe-marin")
    assert prof.revisions.count() == 1  # created only — no phantom history


@pytest.mark.django_db
def test_archive_is_the_delete_and_hides_from_public(client):
    client.post(LIST_URL, _payload(), format="json")
    resp = client.post(f"{LIST_URL}cartographe-marin/archive/")
    assert resp.status_code == 200
    prof = Profession.objects.get(slug="cartographe-marin")
    assert prof.status == ProfessionStatus.ARCHIVED
    assert prof.is_active is False
    assert prof.revisions.filter(action="status_changed").exists()
    assert Profession.objects.filter(slug="cartographe-marin").exists()  # never hard-deleted


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rollback_restores_fields_and_appends_history(client):
    client.post(LIST_URL, _payload(), format="json")
    prof = Profession.objects.get(slug="cartographe-marin")
    first_revision = prof.revisions.get()

    client.patch(
        f"{LIST_URL}cartographe-marin/",
        {"name": "Cartographe des abysses", "median_salary_eur": 40000},
        format="json",
    )
    resp = client.post(f"{LIST_URL}cartographe-marin/rollback/{first_revision.pk}/")
    assert resp.status_code == 200

    prof.refresh_from_db()
    assert prof.name == "Cartographe marin"  # restored
    assert prof.median_salary_eur == 32000
    revs = list(prof.revisions.order_by("created_at"))
    assert [r.action for r in revs] == ["created", "updated", "rolled_back"]
    assert revs[-1].restored_from_id == first_revision.pk
    assert AuditLog.objects.filter(action="referential.profession_rolled_back").exists()


@pytest.mark.django_db
def test_rollback_refuses_a_foreign_revision(client):
    client.post(LIST_URL, _payload("metier-a"), format="json")
    client.post(LIST_URL, _payload("metier-b", name="Métier B"), format="json")
    foreign = Profession.objects.get(slug="metier-b").revisions.get()
    resp = client.post(f"{LIST_URL}metier-a/rollback/{foreign.pk}/")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# List: search / filter / sort
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_searches_filters_and_covers_all_statuses(client):
    client.post(LIST_URL, _payload("publie-91", name="Océanographe"), format="json")
    client.post(
        LIST_URL, _payload("brouillon-92", name="Vulcanologue", status="draft"), format="json"
    )
    client.post(
        LIST_URL, _payload("archive-93", name="Télégraphiste", status="archived"), format="json"
    )

    everything = client.get(LIST_URL).json()
    slugs = {r["slug"] for r in everything["results"]}
    assert {"publie-91", "brouillon-92", "archive-93"} <= slugs  # all statuses listed

    drafts = client.get(LIST_URL, {"status": "draft"}).json()["results"]
    assert [r["slug"] for r in drafts] == ["brouillon-92"]

    searched = client.get(LIST_URL, {"q": "océano"}).json()["results"]
    assert [r["slug"] for r in searched] == ["publie-91"]
