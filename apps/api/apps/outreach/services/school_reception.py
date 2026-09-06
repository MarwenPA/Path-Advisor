"""School-side reception of early-outreach requests — Story 5.6.

The RBAC boundary (NFR-S4 — "école ne voit ni les autres recos de l'élève,
ni les autres écoles ciblées") is structural, not something this service
has to enforce by filtering fields: `EarlyOutreachRequest` never stores the
student's other recommendations or other targeted schools in the first
place (§2 scope decision from Story 5.4). What this module DOES enforce is
the tenant boundary — a school admin only ever sees rows for *their own*
school (`get_school_for_admin` + `list_school_outreach_requests` scoping by
`school=`).

Data-access rationale (RLS, Story 1.8): a school-admin request runs under
`app.current_user_id = <that admin's id>` — the `users` table's RLS policy
makes every OTHER user's row (incl. the student's) invisible to that
session, so `select_related("student")` would silently drop rows via the
JOIN. Both listing functions wrap the query in `bypass_rls` AFTER the
`school=` scoping is already applied — the business authorization here is
"this row belongs to your school", not the RLS policy (same rationale as
`apps.family.services.parent_view`).
"""

from __future__ import annotations

from apps.core.rls import bypass_rls
from apps.outreach.exceptions import SchoolStaffNotLinked
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachRequestStatus
from apps.schools.models import School, SchoolStaff

# Requests still in these statuses aren't visible to the school yet — either
# the motivation hasn't cleared moderation, or it never will (Story 5.5).
_RECEIVABLE_STATUSES = frozenset(
    {
        EarlyOutreachRequestStatus.PENDING,
        EarlyOutreachRequestStatus.RESPONDED,
        EarlyOutreachRequestStatus.EXPIRED_7D,
    }
)


def get_school_for_admin(*, user) -> School:
    """Resolve the one school a `SCHOOL_ADMIN` user represents."""
    staff = SchoolStaff.objects.select_related("school").filter(user=user).first()
    if staff is None:
        raise SchoolStaffNotLinked()
    return staff.school


def list_school_outreach_requests(
    *, school: School, status: str | None = None, ordering: str = "-created_at"
) -> list[EarlyOutreachRequest]:
    """AC — reception queue, most recent first by default. `status` filters
    to one value; an unrecognized `ordering` falls back to `-created_at`
    rather than raising (a stray query param shouldn't 500 the queue).

    Returns an already-evaluated list (not a lazy `QuerySet`) — the
    `bypass_rls` context must close before the view's pagination re-queries
    it, and DRF's `PageNumberPagination` slices a plain list just fine.
    """
    qs = EarlyOutreachRequest.objects.filter(
        school=school, status__in=_RECEIVABLE_STATUSES
    ).select_related("profession", "parcours", "student")
    if status:
        qs = qs.filter(status=status)
    if ordering not in {"created_at", "-created_at"}:
        ordering = "-created_at"
    with bypass_rls(reason="school_reception.list_school_outreach_requests"):
        return list(qs.order_by(ordering))


def get_school_outreach_request(*, school: School, outreach_id: str) -> EarlyOutreachRequest:
    """Detail lookup, scoped to `school` + the receivable statuses — a
    `pending_moderation`/`rejected` request 404s for the school exactly as
    if it didn't exist (it isn't theirs to see yet)."""
    with bypass_rls(reason="school_reception.get_school_outreach_request"):
        return EarlyOutreachRequest.objects.select_related("profession", "parcours", "student").get(
            school=school, id=outreach_id, status__in=_RECEIVABLE_STATUSES
        )
