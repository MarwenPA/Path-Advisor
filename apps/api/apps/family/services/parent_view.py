"""Parent read-only view service — Story 6.2 §T2.

Owns every read a linked parent performs on a child's data. The invariant is
that authorization comes ONLY from a non-revoked `ParentStudentLink` (Story
6.1 §AC7) — never from email, tenant, or role alone.

Data-access rationale (RLS, Story 1.8):
    A parent request runs under `app.current_user_id = parent.id`. The child's
    `users` / `student_profiles` / `favorite_schools` rows are invisible to
    that session. Every child-data read here is wrapped in `bypass_rls` AFTER
    the link check — the business authorization is the link, not the RLS
    policy (same rationale as `ParentLinkSource`, Story 6.1).

Confidentiality frontier (FR41 / AC2 / AC3):
    Nothing in this module exposes a bulletin field. `compute_recommendations`
    reads a bulletin *summary* internally but returns only id/slug/name/
    sector/score/confidence/signals. `get_child_mes_paris` returns public
    School referential rows. No teacher appreciation / raw grade ever leaves.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.accounts.models import User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.rls import bypass_rls
from apps.core.text import mask_email
from apps.family.exceptions import ParentBulletinsForbidden, ParentNotLinkedToStudent
from apps.family.models import ParentStudentLink
from apps.recommendations.services.ai_client import AIServiceUnavailableError
from apps.recommendations.services.recommendation_service import compute_recommendations
from apps.schools.models import School

log = logging.getLogger(__name__)


def _child_summary(student: User) -> dict[str, Any]:
    """Minimal identity block shown to the parent — no PII beyond the masked
    email + the display handle the student already exposes to invited parents.
    """
    return {
        "id": student.id,
        "first_name": student.email.split("@")[0],
        "masked_email": mask_email(student.email),
    }


def get_linked_children(parent: User) -> list[User]:
    """AC4 — the students this parent is actively (non-revoked) linked to."""
    with bypass_rls(reason="parent_view.list_children"):
        links = list(
            ParentStudentLink.objects.filter(
                parent=parent,
                revoked_at__isnull=True,
            )
            .select_related("student")
            .only("id", "student__id", "student__email")
        )
    return [link.student for link in links]


def resolve_linked_child(parent: User, student_id: str) -> User:
    """AC4 — return the child `User` iff an active link exists, else 403 + audit.

    The non-revoked `ParentStudentLink` is the SOLE authorization source.
    """
    with bypass_rls(reason="parent_view.resolve_link"):
        link = (
            ParentStudentLink.objects.filter(
                parent=parent,
                student_id=student_id,
                revoked_at__isnull=True,
            )
            .select_related("student")
            .first()
        )
    if link is None:
        record_audit(
            action="parent.child_access_denied",
            result=AuditResult.DENIED,
            actor=parent,
            subject_id=student_id,
            metadata={"reason": "no_active_link"},
        )
        raise ParentNotLinkedToStudent()
    return link.student


def get_child_professions(student: User) -> list[dict[str, Any]]:
    """AC1 — "métiers explorés" as compact `ScoreVocationnel` card DTOs.

    Reuses `compute_recommendations` (Epic 3). Degrades gracefully to `[]` if
    the AI service is unavailable — the dashboard must still render mes-paris
    and costs. Exposes NO bulletin field (AC2/AC3).
    """
    try:
        with bypass_rls(reason="parent_view.child_professions"):
            data = compute_recommendations(student)
    except AIServiceUnavailableError:
        log.warning("parent_view.professions_ai_unavailable", extra={"student": student.id})
        return []

    professions: list[dict[str, Any]] = []
    for item in data.get("results", []):
        signals = [
            {"id": str(s.get("id") or s.get("label") or ""), "label": s.get("label", "")}
            if isinstance(s, dict)
            else {"id": str(s), "label": str(s)}
            for s in item.get("signals_contributifs", [])
        ]
        professions.append(
            {
                "metier_id": item.get("id"),
                "slug": item.get("slug"),
                "name": item.get("name"),
                "sector": item.get("sector"),
                "score": item.get("score", 0),
                "confidence_level": item.get("confidence_level", "low"),
                "signals": signals,
                "phrase_recopiable": item.get("phrase_recopiable", ""),
            }
        )
    return professions


def _favorite_schools(student: User) -> list[School]:
    with bypass_rls(reason="parent_view.child_mes_paris"):
        return list(
            School.objects.filter(favorited_by__user=student).order_by("-favorited_by__created_at")
        )


def get_child_mes_paris(student: User) -> list[dict[str, Any]]:
    """AC1 — "Mes paris" = the child's favorited schools (Story 4.8)."""
    return [
        {
            "school_id": str(school.id),
            "slug": school.slug,
            "name": school.name,
            "city": school.city,
            "type": school.type,
            "tuition_min_eur": school.tuition_min_eur,
            "tuition_max_eur": school.tuition_max_eur,
        }
        for school in _favorite_schools(student)
    ]


def get_child_parcours_costs(student: User) -> dict[str, Any]:
    """AC1 — "Coûts estimés des parcours sauvegardés": total + per-school breakdown.

    Sums the tuition ranges of the child's favorited schools. A school with an
    unknown tuition contributes 0 to the totals but still appears in the
    breakdown (with null tuition) so the parent sees the full list.
    """
    schools = _favorite_schools(student)
    total_min = 0
    total_max = 0
    breakdown: list[dict[str, Any]] = []
    for school in schools:
        tmin = school.tuition_min_eur
        tmax = school.tuition_max_eur
        total_min += tmin or 0
        total_max += tmax or 0
        breakdown.append(
            {
                "school_id": str(school.id),
                "school_name": school.name,
                "tuition_min_eur": tmin,
                "tuition_max_eur": tmax,
            }
        )
    return {
        "total_min_eur": total_min,
        "total_max_eur": total_max,
        "count": len(schools),
        "breakdown": breakdown,
    }


def get_child_dashboard(parent: User, student_id: str) -> dict[str, Any]:
    """AC1 — orchestrate the 3 parent-visible sections + audit the access."""
    student = resolve_linked_child(parent, student_id)

    dashboard = {
        "child": _child_summary(student),
        "metiers_explores": get_child_professions(student),
        "mes_paris": get_child_mes_paris(student),
        "couts_estimes": get_child_parcours_costs(student),
    }

    record_audit(
        action="parent.child_dashboard_viewed",
        result=AuditResult.SUCCESS,
        actor=parent,
        subject_id=student.id,
        metadata={
            "professions_count": len(dashboard["metiers_explores"]),
            "mes_paris_count": dashboard["couts_estimes"]["count"],
        },
    )
    return dashboard


def deny_bulletins_access(parent: User, student_id: str) -> None:
    """AC3 — a parent may never read a child's bulletins. 403 + dedicated audit.

    Called even for a LINKED parent: the confidentiality frontier (FR41) is
    absolute, independent of the link that grants dashboard access.
    """
    record_audit(
        action="parent.bulletins_access_denied",
        result=AuditResult.DENIED,
        actor=parent,
        subject_id=student_id,
        metadata={"reason": "parent_role_never_sees_bulletins"},
    )
    raise ParentBulletinsForbidden()
