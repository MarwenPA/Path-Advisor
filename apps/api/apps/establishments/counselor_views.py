"""Counselor + student-facing cohort/consent views — Story 6.7 (+ 6.6/6.8/6.9
add more to this module as they land).

Mounted at `api/v1/` via `apps.establishments.cohort_urls` (distinct from
`apps.establishments.urls`, the admin-only B2B onboarding surface at
`api/v1/admin/`).
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status as drf_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import User
from apps.core.permissions import IsCounselor, IsStudent
from apps.core.rls import bypass_rls
from apps.establishments.exceptions import StudentNotInCounselorsEstablishment
from apps.establishments.models import CounselorConsent, StudentImportInvitation
from apps.establishments.serializers import ConsentDecisionSerializer, CounselorConsentSerializer
from apps.establishments.services.counselor_consent import (
    decide_consent,
    list_pending_consent_requests,
    request_consent,
)


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
