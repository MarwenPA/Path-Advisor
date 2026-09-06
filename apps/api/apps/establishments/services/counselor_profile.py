"""Counselor-side individual profile view — Story 6.8.

Gated by `require_granted_consent` (Story 6.7) — every function here
assumes that gate already passed (the view calls it first, propagating
`ConsentNotGranted` as a 403 before anything in this module runs).

Reuses `apps.family.services.parent_view`'s pure, student-only functions
(`get_child_professions`, `get_child_mes_paris`) rather than duplicating
the AI-recommendation/favorites-lookup logic — neither function performs
any parent-specific authorization internally (that lives in
`resolve_linked_child`, never called here), so importing them is safe reuse,
not a layering violation.
"""

from __future__ import annotations

import io
from typing import Any

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from apps.accounts.models import User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.rls import bypass_rls
from apps.establishments.models import CounselorNote, StudentImportInvitation
from apps.establishments.services.counselor_consent import (
    require_granted_consent,
    touch_last_accessed,
)
from apps.family.services.parent_view import get_child_mes_paris, get_child_professions


def get_student_profile_for_counselor(*, counselor: User, student_id: str) -> dict[str, Any]:
    """AC1 — the individual profile a consenting counselor sees.

    Excludes login credentials and payment data (NFR-S4) by construction —
    this dict only ever assembles the fields listed below, never a raw
    `User`/`Subscription` serialization.

    "Vœux en construction" (AC1) is omitted — no such data exists anywhere
    in the codebase yet (no Parcoursup-wish-list model); differed rather
    than faked, same as Story 5.10's Parcoursup-conversion field.
    """
    consent = require_granted_consent(counselor=counselor, student_id=student_id)

    with bypass_rls(reason="counselor_profile.resolve_student"):
        student = User.objects.get(id=student_id)
        invitation = (
            StudentImportInvitation.objects.select_related("cohort")
            .filter(user_id=student_id)
            .first()
        )

    profile = {
        "student_id": student.id,
        "cohort_name": invitation.cohort.name if invitation else None,
        "metiers_top_recos": get_child_professions(student),
        "mes_paris": get_child_mes_paris(student),
        "activite_recente": {"derniere_connexion": student.last_login},
        "voeux_en_construction": [],
    }

    touch_last_accessed(consent)
    record_audit(
        action="establishments.counselor_profile_viewed",
        result=AuditResult.SUCCESS,
        actor=counselor,
        subject_id=student_id,
        metadata={"consent_id": consent.id},
    )
    return profile


def add_counselor_note(*, counselor: User, student_id: str, text: str) -> CounselorNote:
    """AC — private note, gated the same way the profile view is (a
    counselor without granted consent has no business annotating a
    student they can't see)."""
    require_granted_consent(counselor=counselor, student_id=student_id)
    return CounselorNote.objects.create(counselor=counselor, student_id=student_id, text=text)


def list_counselor_notes(*, counselor: User, student_id: str) -> list[CounselorNote]:
    require_granted_consent(counselor=counselor, student_id=student_id)
    return list(CounselorNote.objects.filter(counselor=counselor, student_id=student_id))


def export_interview_sheet_pdf(*, counselor: User, student_id: str) -> bytes:
    """AC — "fiche entretien PDF (synthèse profil + mes notes) pour usage
    interne". A single-page, text-only PDF (reportlab's low-level canvas —
    no page-layout library beyond what's needed for this one document) —
    proportionate to the actual need, not a general-purpose report engine.
    """
    profile = get_student_profile_for_counselor(counselor=counselor, student_id=student_id)
    notes = list_counselor_notes(counselor=counselor, student_id=student_id)

    buffer = io.BytesIO()
    doc = canvas.Canvas(buffer, pagesize=A4)
    _width, height = A4
    y = height - 2 * cm

    def line(text: str, *, size: int = 11, gap: float = 0.6 * cm) -> None:
        nonlocal y
        doc.setFont("Helvetica", size)
        doc.drawString(2 * cm, y, text)
        y -= gap

    line("Fiche entretien — Path-Advisor", size=16, gap=1 * cm)
    line(f"Cohorte : {profile['cohort_name'] or '—'}")
    line(f"Généré le : {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    line("")
    line("Métiers Top recos :", size=13)
    for m in profile["metiers_top_recos"]:
        line(f"  • {m['name']} ({m['score']}%)")
    line("")
    line("Mes paris (écoles sauvegardées) :", size=13)
    for s in profile["mes_paris"]:
        line(f"  • {s['name']} — {s['city']}")
    line("")
    line("Notes personnelles :", size=13)
    for note in notes:
        line(f"  • {note.text[:200]}")

    doc.showPage()
    doc.save()
    return buffer.getvalue()
