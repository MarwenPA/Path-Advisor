"""Story 10.1 — at-risk student detection for the counselor dashboard.

Three rules from the epic (FR-FF1), each EXPLAINED, never opaque:

- ``faible_engagement`` — no login for 30 days. Derived from
  ``User.last_login``, the exact signal the 6.6 dashboard already exposes
  per student to same-tenant counselors ("activité récente"), so this rule
  applies to the WHOLE cohort, consent or not.
- ``profil_incoherent`` / ``baisse_moyenne`` — derived from profile choices
  and grades: INDIVIDUAL data, the 6.7/6.8 territory. These two rules run
  ONLY for students whose consent is GRANTED — the consent boundary follows
  the data, not the screen. The response carries how many students were
  only shallow-checked so the counselor knows the list's limits.

Dignity by construction (AC3): this module emits reason CODES + numbers;
the UI renders constructive wording ("nécessite ton attention"), and no
student-facing path reads any of it.

Computed on demand at dashboard load (lazy, the Epic-10 pattern) — cohort
sizes are double digits, and the queries below are batched (no per-student
AI calls, unlike ``top_metiers``).
"""

from __future__ import annotations

from typing import Any

import structlog
from django.utils import timezone

from apps.accounts.models import User
from apps.bulletins.models import BulletinManual
from apps.core.rls import bypass_rls
from apps.students.models import StudentLevelProfile, StudentProfile
from apps.students.onboarding.levels import SPECIALITE_IDS

from ..models import (
    CounselorConsent,
    CounselorConsentStatus,
    CounselorIntervention,
    StudentImportInvitation,
    StudentImportInvitationStatus,
)

log = structlog.get_logger(__name__)

ENGAGEMENT_INACTIVE_DAYS = 30
GRADE_DROP_THRESHOLD = 2.0
#: The incoherence rule needs at least this many MAPPED passions before it
#: dares say anything — one hobby with no matching spécialité is normal
#: teenage life, not a risk signal.
MIN_MAPPED_PASSIONS = 2

#: Editorial v1 affinity map (consigned in the story doc): which spécialités
#: "cover" each onboarding passion. Deliberately conservative — strong,
#: uncontroversial links only. Passions with no natural GT spécialité
#: (cuisine…) are absent on purpose: they never count against a student.
PASSION_SPECIALITE_AFFINITY: dict[str, frozenset[str]] = {
    "sciences-nature": frozenset({"svt", "physique-chimie", "bio-ecologie", "mathematiques"}),
    "tech-code": frozenset({"nsi", "mathematiques", "si"}),
    "arts-creation": frozenset({"arts", "hlp"}),
    "sport-corps": frozenset({"eppcs", "svt"}),
    "aider-autres": frozenset({"ses", "svt", "hlp"}),
    "musique": frozenset({"arts"}),
    "cinema-series": frozenset({"arts", "hlp", "llcer"}),
    "lecture-ecriture": frozenset({"hlp", "llca", "llcer", "hggsp"}),
    "voyage-cultures": frozenset({"llcer", "hggsp", "hlp"}),
    "mode-style": frozenset({"arts"}),
    "business-argent": frozenset({"ses", "mathematiques"}),
    "jeux-video": frozenset({"nsi", "mathematiques", "arts"}),
    "animaux": frozenset({"svt", "bio-ecologie"}),
    "education-transmission": frozenset({"hlp", "ses"}),
    "sante-soin": frozenset({"svt", "physique-chimie", "bio-ecologie"}),
    "politique-societe": frozenset({"hggsp", "ses", "hlp"}),
    "bricolage-mains": frozenset({"si", "physique-chimie"}),
    "communication-media": frozenset({"hggsp", "ses", "hlp", "llcer"}),
    "spiritualite-sens": frozenset({"hlp", "hggsp"}),
}


def _engagement_reason(student: User, accepted_at: Any) -> dict[str, Any] | None:
    """> 30 days without a login. A student who NEVER logged in counts from
    their invitation acceptance — silence since day one is the strongest
    disengagement signal, not a blind spot."""
    reference = student.last_login or accepted_at
    if reference is None:
        return None
    days = (timezone.now() - reference).days
    if days > ENGAGEMENT_INACTIVE_DAYS:
        return {"code": "faible_engagement", "days_inactive": days}
    return None


def _incoherence_reason(
    profile: StudentProfile | None, level_profile: StudentLevelProfile | None
) -> dict[str, Any] | None:
    """Zero overlap between the spécialités covering the student's passions
    and the spécialités they chose. GT vocabulary only — bac-pro spécialités
    live in another referential and are skipped (consigned)."""
    if profile is None or level_profile is None:
        return None
    passions = [p for p in (profile.passions or []) if isinstance(p, str)]
    specialites = {s for s in (level_profile.specialites or []) if isinstance(s, str)}
    if not specialites or not specialites <= SPECIALITE_IDS:
        return None
    mapped = [p for p in passions if p in PASSION_SPECIALITE_AFFINITY]
    if len(mapped) < MIN_MAPPED_PASSIONS:
        return None
    covered: set[str] = set()
    for passion in mapped:
        covered |= PASSION_SPECIALITE_AFFINITY[passion]
    if covered & specialites:
        return None
    return {"code": "profil_incoherent", "nb_passions": len(mapped)}


def _bulletin_average(bulletin: BulletinManual) -> float | None:
    notes = []
    for matiere in bulletin.matieres or []:
        try:
            notes.append(float(matiere["note"]))
        except (KeyError, TypeError, ValueError):
            continue
    return round(sum(notes) / len(notes), 2) if notes else None


def _grade_drop_reason(bulletins: list[BulletinManual]) -> dict[str, Any] | None:
    """Average dropped by more than 2 points between the two most recent
    bulletins (chronological by created_at — `trimestre_label` is free text,
    consigned)."""
    averages = [avg for b in bulletins if (avg := _bulletin_average(b)) is not None]
    if len(averages) < 2:
        return None
    previous, latest = averages[-2], averages[-1]
    drop = round(previous - latest, 2)
    if drop > GRADE_DROP_THRESHOLD:
        return {
            "code": "baisse_moyenne",
            "drop": drop,
            "from_average": previous,
            "to_average": latest,
        }
    return None


def get_at_risk_students(*, counselor: User) -> dict[str, Any]:
    """The "Profils à risque" payload for one counselor's establishment."""
    if counselor.tenant_id is None:
        # A counselor without an establishment has no cohort to watch.
        return {"students": [], "students_without_consent": 0}
    with bypass_rls(reason="risk_detection.resolve_cohort_students"):
        invitations = list(
            StudentImportInvitation.objects.filter(
                status=StudentImportInvitationStatus.ACCEPTED,
                cohort__establishment_id=counselor.tenant_id,
            ).select_related("cohort")
        )
        student_ids = [inv.user_id for inv in invitations]
        students = {u.id: u for u in User.objects.filter(id__in=student_ids)}
        consented_ids = set(
            CounselorConsent.objects.filter(
                counselor=counselor,
                student_id__in=student_ids,
                status=CounselorConsentStatus.GRANTED,
                revoked_at__isnull=True,
            ).values_list("student_id", flat=True)
        )
        profiles = {p.user_id: p for p in StudentProfile.objects.filter(user_id__in=consented_ids)}
        level_profiles = {
            lp.profile.user_id: lp
            for lp in StudentLevelProfile.objects.filter(
                profile__user_id__in=consented_ids
            ).select_related("profile")
        }
        bulletins_by_student: dict[str, list[BulletinManual]] = {}
        for bulletin in BulletinManual.objects.filter(student__user_id__in=consented_ids).order_by(
            "created_at"
        ):
            bulletins_by_student.setdefault(bulletin.student.user_id, []).append(bulletin)

    interventions = {
        row.student_id: row
        for row in CounselorIntervention.objects.filter(
            counselor=counselor, student_id__in=student_ids
        )
    }

    entries: list[dict[str, Any]] = []
    for invitation in invitations:
        sid = invitation.user_id
        student = students.get(sid)
        if student is None:
            continue
        reasons = []
        if (r := _engagement_reason(student, invitation.accepted_at)) is not None:
            reasons.append(r)
        if sid in consented_ids:
            if (r := _incoherence_reason(profiles.get(sid), level_profiles.get(sid))) is not None:
                reasons.append(r)
            if (r := _grade_drop_reason(bulletins_by_student.get(sid, []))) is not None:
                reasons.append(r)
        if not reasons:
            continue
        intervention = interventions.get(sid)
        entries.append(
            {
                "student_id": sid,
                "cohort_name": invitation.cohort.name,
                "reasons": reasons,
                "consent_granted": sid in consented_ids,
                "intervention_in_progress": bool(intervention and intervention.in_progress),
            }
        )

    # Alerting students first, then "intervention en cours"; most reasons on top.
    entries.sort(key=lambda e: (e["intervention_in_progress"], -len(e["reasons"])))
    unconsented = len(student_ids) - len(consented_ids)
    return {
        "students": entries,
        # The counselor must know the list's limits (AC "motif expliqué"):
        # without consent, only the engagement rule could run.
        "students_without_consent": unconsented,
    }
