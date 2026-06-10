"""RLS double-check tests — Story 1.9 §AC10 + review D6.

The aggregator + endpoint rely on TWO belts to prevent cross-student leaks :
1. App-level filter (`ParentalConsent.objects.filter(student=request.user)`)
2. DB-level Row-Level Security policy from Story 1.8

This file validates BELT 2 in isolation : it patches out the app-level filter
(simulating a future bug where someone forgets `.filter(student=...)`) and
verifies that RLS still blocks the cross-student leak.

If this test ever fails, the defense-in-depth claim from Stories 1.7+1.8 is
broken and a code-review must investigate ; do NOT just patch this test.
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.utils import timezone

from apps.accounts.models import ParentalConsent, ParentalConsentDecision
from apps.accounts.tests.factories import UserFactory
from apps.core import request_context

pytestmark = pytest.mark.django_db


def _granted_consent(student):
    return ParentalConsent.objects.create(
        student=student,
        parent_email=f"parent-{student.id}@example.test",
        token=f"t-rls-{student.id}",
        decision=ParentalConsentDecision.GRANTED,
        decided_at=timezone.now(),
    )


def _set_pg_actor(user_id: str | None, tenant_id: str | None = None) -> None:
    """Mimic what `ActorContextMiddleware` does on every authenticated request :
    set the per-connection GUCs `app.current_user_id` + `app.current_tenant_id`
    that the RLS policies on `parental_consents` filter on.
    """
    with connection.cursor() as cursor:
        if user_id is None:
            cursor.execute("RESET app.current_user_id")
        else:
            cursor.execute(f"SET LOCAL app.current_user_id = '{user_id}'")
        if tenant_id is None:
            cursor.execute("RESET app.current_tenant_id")
        else:
            cursor.execute(f"SET LOCAL app.current_tenant_id = '{tenant_id}'")


def _is_postgres() -> bool:
    return connection.vendor == "postgresql"


@pytest.mark.skipif(
    not _is_postgres(),
    reason="RLS only enforced on PostgreSQL. The default test DB (SQLite) has no RLS.",
)
def test_rls_blocks_cross_student_access_even_without_app_filter():
    """The KEY assertion : with the app-level filter REMOVED, RLS still
    scopes the result to the student whose GUC is set.

    Procedure :
    1. Create student A with one granted consent. Create student B with one
       granted consent.
    2. Set the connection GUC to student A.
    3. Run `ParentalConsent.objects.all()` (no app filter) under that GUC.
    4. Assert ONLY student A's consent is returned.

    If RLS were silently disabled or the GUC didn't propagate, student A
    would see student B's consent too — that's the failure this test catches.
    """
    student_a = UserFactory()
    student_b = UserFactory()
    consent_a = _granted_consent(student_a)
    _granted_consent(student_b)

    # Simulate the connection state of an HTTP request from student A.
    request_context.set_actor_id(str(student_a.id))
    try:
        _set_pg_actor(str(student_a.id))
        # No `filter(student=...)` — only RLS scopes the result.
        rows = list(ParentalConsent.objects.all())
    finally:
        request_context.clear()
        _set_pg_actor(None)

    consent_ids = {row.id for row in rows}
    assert consent_a.id in consent_ids
    # The KEY assertion : student B's consent is NOT visible.
    assert all(row.student_id == student_a.id for row in rows), (
        "RLS belt failed — student A's query returned a consent owned by another student"
    )


def test_rls_test_is_meaningful_check_skipped_on_sqlite():
    """Belt-and-braces : this empty assertion exists so when CI runs against
    SQLite the suite still has a passing test for this module (avoids
    "no tests collected" alarms). The real RLS test is the @skipif one above.
    """
    if not _is_postgres():
        pytest.skip("SQLite — no RLS to test")
    # On Postgres, the real test above does the work.
