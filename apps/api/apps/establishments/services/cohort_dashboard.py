"""Cohort dashboard — Story 6.6 (dashboard cohorte conseillère B2B).

Aggregates across all accepted `StudentImportInvitation`s in the
counselor's own establishment (`counselor.tenant_id`) — a counselor with
several cohorts sees them combined, matching "mon dashboard" (singular) in
the AC rather than a per-cohort picker (no such picker is asked for).

Scope decisions:
- **"Métiers les plus explorés"** — no view/click-tracking model exists
  anywhere in the codebase (no `ProfessionView`/analogous event log). Used
  as a proxy: each student's rank-#1 AI-recommended métier (the same
  `compute_recommendations` engine Story 6.8 already reuses), aggregated
  by count across the cohort. Documented, not silently approximated.
- **"Mode dégradé"** — no such flag exists on `User`/`StudentProfile`.
  Defined as `onboarding_step1_status != COMPLETED` (the AI-scoring
  fallback documented in `recommendation_service.compute_recommendations`
  — "missing profile → empty profile dict sent to ai-service" — only
  triggers for a student who hasn't finished step 1).
- **"Distribution filière"** — `StudentLevelProfile.filiere`, `None`
  bucketed as "Non renseigné".
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from apps.accounts.models import User
from apps.core.rls import bypass_rls
from apps.establishments.models import StudentImportInvitation, StudentImportInvitationStatus
from apps.students.models import OnboardingStep1Status, StudentLevelProfile, StudentProfile


def get_cohort_dashboard(*, counselor: User) -> dict[str, Any]:
    with bypass_rls(reason="cohort_dashboard.resolve_cohort_students"):
        invitations = list(
            StudentImportInvitation.objects.filter(
                status=StudentImportInvitationStatus.ACCEPTED,
                cohort__establishment_id=counselor.tenant_id,
            ).select_related("cohort", "user")
        )
        student_ids = [inv.user_id for inv in invitations]
        students = {u.id: u for u in User.objects.filter(id__in=student_ids)}
        profiles = {p.user_id: p for p in StudentProfile.objects.filter(user_id__in=student_ids)}
        level_profiles = {
            lp.profile.user_id: lp
            for lp in StudentLevelProfile.objects.filter(
                profile__user_id__in=student_ids
            ).select_related("profile")
        }

    total = len(student_ids)
    completed = sum(
        1
        for sid in student_ids
        if (p := profiles.get(sid)) is not None
        and p.onboarding_step1_status == OnboardingStep1Status.COMPLETED
    )
    degraded = total - completed

    filiere_counter: Counter[str] = Counter()
    for sid in student_ids:
        lp = level_profiles.get(sid)
        filiere_counter[lp.filiere if lp and lp.filiere else "Non renseigné"] += 1

    metier_counter: Counter[str] = Counter()
    for sid in student_ids:
        student = students.get(sid)
        if student is None:
            continue
        try:
            from apps.family.services.parent_view import get_child_professions

            top = get_child_professions(student)
        except Exception:
            top = []
        if top:
            metier_counter[top[0]["name"]] += 1

    recent_activity = sorted(
        (
            {"student_id": sid, "derniere_connexion": students[sid].last_login}
            for sid in student_ids
            if sid in students and students[sid].last_login is not None
        ),
        key=lambda row: row["derniere_connexion"],
        reverse=True,
    )[:10]

    return {
        "kpis": {
            "nb_eleves": total,
            "taux_completion_profil": round(100 * completed / total, 1) if total else 0.0,
            "nb_eleves_mode_degrade": degraded,
        },
        "top_metiers": [
            {"name": name, "count": count} for name, count in metier_counter.most_common(10)
        ],
        "distribution_filiere": [
            {"filiere": filiere, "count": count} for filiere, count in filiere_counter.most_common()
        ],
        "activite_recente": recent_activity,
        "eleves": [
            {
                "student_id": sid,
                "cohort_name": inv.cohort.name,
            }
            for inv, sid in zip(invitations, student_ids, strict=True)
        ],
    }
