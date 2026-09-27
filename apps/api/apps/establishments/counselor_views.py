"""Counselor + student-facing cohort/consent views — Story 6.7 (+ 6.6/6.8/6.9
add more to this module as they land).

Mounted at `api/v1/` via `apps.establishments.cohort_urls` (distinct from
`apps.establishments.urls`, the admin-only B2B onboarding surface at
`api/v1/admin/`).
"""

from __future__ import annotations

from typing import cast

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status as drf_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsCounselor, IsStudent
from apps.core.rls import bypass_rls
from apps.establishments.exceptions import StudentNotInCounselorsEstablishment
from apps.establishments.models import (
    CounselorConsent,
    CounselorIntervention,
    StudentImportInvitation,
)
from apps.establishments.serializers import (
    CohortDashboardSerializer,
    ConsentDecisionSerializer,
    CounselorConsentSerializer,
    CounselorNoteCreateSerializer,
    CounselorNoteSerializer,
    CounselorStudentProfileSerializer,
)
from apps.establishments.services.cohort_dashboard import get_cohort_dashboard
from apps.establishments.services.cohort_reporting_export import export_cohort_reporting_csv
from apps.establishments.services.counselor_consent import (
    decide_consent,
    list_pending_consent_requests,
    request_consent,
)
from apps.establishments.services.counselor_profile import (
    add_counselor_note,
    export_interview_sheet_pdf,
    get_student_profile_for_counselor,
    list_counselor_notes,
)
from apps.establishments.services.risk_detection import get_at_risk_students


@api_view(["POST"])
@permission_classes([IsCounselor])
def counselor_consent_request(request: Request, student_id: str) -> Response:
    """POST /api/v1/establishments/students/{student_id}/consent-request/ —
    Story 6.7 AC. `cohort_id` is resolved server-side from the student's own
    accepted `StudentImportInvitation` — never accepted from the client (the
    same "server-side resolution over a manual picker" scope decision as
    Story 5.4's parcours field). The actual authorization is the tenant
    match below — a counselor may only request consent from a student in
    their own establishment.

    `bypass_rls` — `student_import_invitations` has FORCE RLS (migration
    0003); a counselor's session isn't automatically granted SELECT on
    another tenant member's row via a plain filter. The tenant-match check
    right after is the real authorization, not the RLS policy — same
    rationale as `apps.family.services.parent_view`.
    """
    with bypass_rls(reason="counselor_views.resolve_invitation_for_consent_request"):
        invitation = get_object_or_404(
            StudentImportInvitation.objects.select_related("cohort"),
            user_id=student_id,
            status="accepted",
        )
        student = get_object_or_404(User, id=student_id)

    if invitation.cohort.establishment_id != request.user.tenant_id:
        raise StudentNotInCounselorsEstablishment()

    consent = request_consent(
        counselor=request.user,
        student=student,
        cohort_id=invitation.cohort_id,
    )
    return Response(CounselorConsentSerializer(consent).data, status=drf_status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsStudent])
def student_pending_consents(request: Request) -> Response:
    """GET /api/v1/establishments/consent-requests/ — the student's own
    pending requests, to render the `ConsentDialog`."""
    consents = list_pending_consent_requests(student=request.user)
    return Response(CounselorConsentSerializer(consents, many=True).data)


@api_view(["POST"])
@permission_classes([IsStudent])
def student_decide_consent(request: Request, consent_id: str) -> Response:
    """POST /api/v1/establishments/consent-requests/{id}/decide/ — AC."""
    serializer = ConsentDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    consent = get_object_or_404(CounselorConsent, id=consent_id, student=request.user)
    decided = decide_consent(
        student=request.user,
        consent_id=consent.id,
        granted=serializer.validated_data["granted"],
    )
    return Response(CounselorConsentSerializer(decided).data)


@api_view(["GET"])
@permission_classes([IsCounselor])
def counselor_cohort_dashboard(request: Request) -> Response:
    """GET /api/v1/establishments/cohort-dashboard/ — Story 6.6 AC. Combines
    every accepted student across all of the counselor's own establishment's
    cohorts (see `cohort_dashboard.py` module docstring for the "top métiers"
    and "mode dégradé" scope decisions)."""
    dashboard = get_cohort_dashboard(counselor=request.user)
    return Response(CohortDashboardSerializer(dashboard).data)


@api_view(["GET"])
@permission_classes([IsCounselor])
def counselor_cohort_reporting_export(request: Request) -> HttpResponse:
    """GET /api/v1/establishments/cohort-dashboard/export.csv/ — Story 6.9
    AC. Aggregate-only, k-anonymized (see `cohort_reporting_export.py`)."""
    csv_bytes = export_cohort_reporting_csv(counselor=request.user)
    response = HttpResponse(csv_bytes, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporting-cohorte.csv"'
    return response


@api_view(["GET"])
@permission_classes([IsCounselor])
def counselor_student_profile(request: Request, student_id: str) -> Response:
    """GET /api/v1/establishments/students/{student_id}/profile/ — Story 6.8
    AC1. `ConsentNotGranted` (403, global RFC7807 handler) if the counselor
    doesn't have a granted, non-revoked consent — the caller (Story 6.6's
    dashboard) is responsible for offering "Demander le consentement"
    instead of retrying this endpoint blindly."""
    profile = get_student_profile_for_counselor(counselor=request.user, student_id=student_id)
    return Response(CounselorStudentProfileSerializer(profile).data)


@api_view(["GET", "POST"])
@permission_classes([IsCounselor])
def counselor_student_notes(request: Request, student_id: str) -> Response:
    """GET/POST /api/v1/establishments/students/{student_id}/notes/ — Story
    6.8 AC2. Private to the authoring counselor — never readable by the
    student or any other counselor."""
    if request.method == "POST":
        serializer = CounselorNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = add_counselor_note(
            counselor=request.user,
            student_id=student_id,
            text=serializer.validated_data["text"],
        )
        return Response(CounselorNoteSerializer(note).data, status=drf_status.HTTP_201_CREATED)

    notes = list_counselor_notes(counselor=request.user, student_id=student_id)
    return Response(CounselorNoteSerializer(notes, many=True).data)


@api_view(["GET"])
@permission_classes([IsCounselor])
def counselor_interview_sheet_pdf(request: Request, student_id: str) -> HttpResponse:
    """GET /api/v1/establishments/students/{student_id}/interview-sheet.pdf/
    — Story 6.8 AC2 (export)."""
    pdf_bytes = export_interview_sheet_pdf(counselor=request.user, student_id=student_id)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="fiche-entretien-{student_id}.pdf"'
    return response


@api_view(["GET"])
@permission_classes([IsCounselor])
def counselor_at_risk_students(request: Request) -> Response:
    """GET /api/v1/establishments/cohort-dashboard/at-risk/ — Story 10.1.

    Reason CODES + numbers only; the UI owns the constructive wording (AC3).
    Individual-data rules (profil/bulletins) run only for consent-granted
    students — the response says how many were engagement-checked only.
    Audited: this list derives individual signals, like the 6.8 profile view.
    """
    counselor = cast(User, request.user)
    payload = get_at_risk_students(counselor=counselor)
    record_audit(
        action="establishments.at_risk_list_viewed",
        result=AuditResult.SUCCESS,
        actor=counselor,
        metadata={
            "flagged": len(payload["students"]),
            "without_consent": payload["students_without_consent"],
        },
    )
    return Response(payload)


@api_view(["POST", "DELETE"])
@permission_classes([IsCounselor])
def counselor_student_intervention(request: Request, student_id: str) -> Response:
    """POST/DELETE /api/v1/establishments/students/{student_id}/intervention/
    — Story 10.1. POST marks (or reopens) "intervention en cours"; DELETE
    resolves it, both idempotent. Establishment membership is the
    authorization (same check as the consent request) — no consent needed:
    the marker is the counselor's OWN workflow state, not student data.
    """
    with bypass_rls(reason="counselor_views.resolve_invitation_for_intervention"):
        invitation = get_object_or_404(
            StudentImportInvitation.objects.select_related("cohort"),
            user_id=student_id,
            status="accepted",
        )
        student = get_object_or_404(User, id=student_id)

    if invitation.cohort.establishment_id != cast(User, request.user).tenant_id:
        raise StudentNotInCounselorsEstablishment()

    if request.method == "POST":
        intervention, created = CounselorIntervention.objects.get_or_create(
            counselor_id=request.user.pk, student=student
        )
        if not created and intervention.resolved_at is not None:
            intervention.resolved_at = None
            intervention.save(update_fields=["resolved_at", "updated_at"])
        record_audit(
            action="establishments.intervention_marked",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject_id=student_id,
            metadata={"intervention_id": intervention.id},
        )
        return Response(
            {"intervention_in_progress": True},
            status=drf_status.HTTP_201_CREATED if created else drf_status.HTTP_200_OK,
        )

    updated = CounselorIntervention.objects.filter(
        counselor_id=request.user.pk, student_id=student_id, resolved_at__isnull=True
    ).update(resolved_at=timezone.now())
    if updated:
        record_audit(
            action="establishments.intervention_resolved",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject_id=student_id,
        )
    return Response(status=drf_status.HTTP_204_NO_CONTENT)
