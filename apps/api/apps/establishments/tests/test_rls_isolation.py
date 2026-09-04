"""Story 6.5 §T8.5 / AC6 — RLS isolation for `establishments` + `cohorts`.

Requires a real PostgreSQL backend (`make test-rls`) — same contract as
`apps.accounts.tests.test_rls_isolation`. Marked `postgresql_only` + `rls`.
"""

from __future__ import annotations

import pytest
from django.db import connection, transaction

from apps.accounts.models import UserRole
from apps.core.rls import bypass_rls
from apps.establishments.models import Cohort, Establishment, EstablishmentType, LicenseType

pytestmark = [pytest.mark.postgresql_only, pytest.mark.rls]


def _set_gucs(cursor, *, user_id: str = "", tenant_id: str = "", actor_role: str = "") -> None:
    cursor.execute(
        "SELECT "
        "set_config('app.current_user_id', %s, true), "
        "set_config('app.current_tenant_id', %s, true), "
        "set_config('app.actor_role', %s, true)",
        [user_id, tenant_id, actor_role],
    )


def _make_establishment(*, uai: str) -> Establishment:
    # Code-review fix (2026-09): this file's own test setup was never
    # wrapped in `bypass_rls` — on a real NOSUPERUSER/NOBYPASSRLS Postgres
    # role, `establishments_isolation_modify` (path_admin/bypass only)
    # refuses the plain INSERT with `InsufficientPrivilege`, so every test
    # in this file failed at setup, proving nothing about isolation. Pattern
    # copied from `apps/family/tests/test_rls_isolation.py`.
    with bypass_rls(reason="test_setup.create_establishment"):
        return Establishment.objects.create(
            name=f"Lycée {uai}",
            type=EstablishmentType.LYCEE,
            city="Paris",
            uai=uai,
            contact_name="Karim",
            contact_email=f"{uai}@ex.test",
            license_start="2026-09-01",
            license_end="2027-08-31",
            license_type=LicenseType.PILOTE_GRATUIT,
        )


def _make_cohort(*, establishment: Establishment, name: str) -> Cohort:
    with bypass_rls(reason="test_setup.create_cohort"):
        return Cohort.objects.create(
            establishment=establishment,
            name=name,
            school_year="2025-2026",
            tenant_id=establishment.id,
            user_id="usr_test_setup",
        )


@pytest.mark.django_db(transaction=True)
def test_cohorts_select_cross_tenant_blocked_for_counselor(skip_if_sqlite):
    """AC6 — a counselor of tenant A must NOT see tenant B's cohorts."""
    establishment_a = _make_establishment(uai="AAA0001")
    establishment_b = _make_establishment(uai="BBB0002")
    cohort_a = _make_cohort(establishment=establishment_a, name="Terminale A")
    cohort_b = _make_cohort(establishment=establishment_b, name="Terminale B")

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id="usr_counselor_a",
            tenant_id=str(establishment_a.id),
            actor_role=UserRole.COUNSELOR,
        )
        cur.execute("SELECT id FROM cohorts")
        visible_ids = {row[0] for row in cur.fetchall()}

    assert cohort_a.id in visible_ids
    assert cohort_b.id not in visible_ids, (
        "RLS cohorts_isolation_select must hide cross-tenant cohorts from a counselor."
    )


@pytest.mark.django_db(transaction=True)
def test_cohorts_select_path_admin_bypasses_rls(skip_if_sqlite):
    establishment_a = _make_establishment(uai="CCC0003")
    establishment_b = _make_establishment(uai="DDD0004")
    cohort_a = _make_cohort(establishment=establishment_a, name="Terminale A")
    cohort_b = _make_cohort(establishment=establishment_b, name="Terminale B")

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur, user_id="usr_admin", tenant_id="", actor_role=UserRole.PATH_ADMIN)
        cur.execute("SELECT id FROM cohorts")
        visible_ids = {row[0] for row in cur.fetchall()}

    assert {cohort_a.id, cohort_b.id}.issubset(visible_ids)


@pytest.mark.django_db(transaction=True)
def test_cohorts_anonymous_session_sees_nothing(skip_if_sqlite):
    establishment = _make_establishment(uai="EEE0005")
    _make_cohort(establishment=establishment, name="Terminale")

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur)
        cur.execute("SELECT id FROM cohorts")
        rows = cur.fetchall()

    assert rows == []


@pytest.mark.django_db(transaction=True)
def test_establishments_select_requires_path_admin_or_bypass(skip_if_sqlite):
    """AC6 — `establishments` has NO same-tenant policy: even a counselor of
    that tenant cannot read the row directly."""
    establishment = _make_establishment(uai="FFF0006")

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(
            cur,
            user_id="usr_counselor",
            tenant_id=str(establishment.id),
            actor_role=UserRole.COUNSELOR,
        )
        cur.execute("SELECT id FROM establishments")
        rows = cur.fetchall()

    assert rows == [], "Counselors must not read `establishments` rows directly (AC6)."


@pytest.mark.django_db(transaction=True)
def test_establishments_select_path_admin_bypasses_rls(skip_if_sqlite):
    establishment = _make_establishment(uai="GGG0007")

    with transaction.atomic(), connection.cursor() as cur:
        _set_gucs(cur, user_id="usr_admin", tenant_id="", actor_role=UserRole.PATH_ADMIN)
        cur.execute("SELECT id FROM establishments WHERE id = %s", [str(establishment.id)])
        rows = cur.fetchall()

    assert len(rows) == 1
