"""Early-outreach API views — Stories 5.4 + 5.5 + 5.6 + 5.7.

Routes:
  POST /api/v1/schools/{slug}/outreach/       — create a request for that school (AC2/AC3/AC5)
  GET  /api/v1/outreach/requests/             — list current user's requests (AC4)
  GET  /api/v1/outreach/quota/                — current-month quota status (AC1/AC3)
  POST /api/v1/outreach/requests/{id}/resubmit/ — student corrects+resubmits a rejected motivation (5.5)
  POST /api/v1/outreach/requests/{id}/interview/accept/  — student accepts a proposed slot (5.7)
  POST /api/v1/outreach/requests/{id}/interview/alternative/ — student proposes another slot (5.7)
  GET  /api/v1/ecole/outreach/                — school's reception queue (5.6)
  GET  /api/v1/ecole/outreach/{id}/            — one request's detail, school-scoped (5.6)
  POST /api/v1/ecole/outreach/{id}/respond/    — school's one-shot response (5.7)

Moderation itself (approve/reject a `pending_moderation` motivation) is a
`path_admin` action exposed via the Django admin (`apps/outreach/admin.py`),
not a separate DRF endpoint — Story 9.4 (back-office admin) is the future
home for a dedicated moderation queue UI; the admin is the interim tool.
"""

from __future__ import annotations

from typing import ClassVar

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services.subscription_service import SubscriptionService
from apps.core.permissions import IsAuthenticatedAndActive, IsSchoolAdmin, IsStudent
from apps.outreach.models import EarlyOutreachRequest
from apps.outreach.serializers import (
    EarlyOutreachCreateSerializer,
    EarlyOutreachListSerializer,
    EarlyOutreachRespondSerializer,
    EarlyOutreachResubmitSerializer,
    EarlyOutreachStudentDetailSerializer,
    EcoleOutreachDetailSerializer,
    EcoleOutreachListSerializer,
    InterviewAcceptSerializer,
    InterviewAlternativeSerializer,
)
from apps.outreach.services.early_outreach import (
    MONTHLY_QUOTA,
    count_outreach_this_month,
    create_early_outreach_request,
    resubmit_early_outreach_motivation,
)
from apps.outreach.services.school_reception import (
    get_school_for_admin,
    get_school_outreach_request,
    list_school_outreach_requests,
)
from apps.outreach.services.school_reporting import (
    build_school_reporting,
    export_school_reporting_csv,
)
from apps.outreach.services.school_response import (
    accept_interview_slot,
    propose_interview_alternative,
    respond_to_outreach_request,
)
from apps.professions.models import Profession
from apps.schools.models import School


class _OutreachPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class SchoolOutreachCreateView(APIView):
    """POST /api/v1/schools/{slug}/outreach/ — AC2/AC3/AC5.

    `IsPremium` deliberately NOT in `permission_classes` (see its own
    docstring): write endpoints use the service-layer gate
    (`SubscriptionService.require_premium`, raises the typed `InsufficientPlan`
    402 the front maps to the contextual paywall) instead of the permission
    class, which would only ever produce a generic 403.
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request: Request, slug: str) -> Response:
        # AC5 — 402 for a freemium user calling this directly (UI bypass).
        SubscriptionService.require_premium(request.user)

        serializer = EarlyOutreachCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        school = get_object_or_404(School, slug=slug)
        profession = get_object_or_404(
            Profession, id=serializer.validated_data["profession_id"], is_active=True
        )

        outreach = create_early_outreach_request(
            student=request.user,
            school=school,
            profession=profession,
            motivation_text=serializer.validated_data["motivation_text"],
        )
        return Response(EarlyOutreachListSerializer(outreach).data, status=201)


class EarlyOutreachListView(APIView):
    """GET /api/v1/outreach/requests/ — AC4, student-scoped."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request) -> Response:
        qs = EarlyOutreachRequest.objects.filter(student=request.user).select_related(
            "school", "profession", "response"
        )
        paginator = _OutreachPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = EarlyOutreachListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class EarlyOutreachDetailView(APIView):
    """GET /api/v1/outreach/requests/{id}/ — Story 5.9 AC (fiche détail).

    Scoped to `student=request.user` — 404 (not 403) for someone else's
    request, same convention as every other student-facing outreach view.
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request, outreach_id: str) -> Response:
        outreach = get_object_or_404(
            EarlyOutreachRequest.objects.select_related("school", "profession", "response"),
            id=outreach_id,
            student=request.user,
        )
        return Response(EarlyOutreachStudentDetailSerializer(outreach).data)


class OutreachQuotaView(APIView):
    """GET /api/v1/outreach/quota/ — AC1/AC3.

    Lets the front decide button-vs-quota-message WITHOUT attempting (and
    catching a 429 from) a POST — a read has no side effect and no risk of
    an accidental extra audit row.
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request) -> Response:
        used = count_outreach_this_month(student=request.user)
        return Response(
            {"used": used, "limit": MONTHLY_QUOTA, "remaining": max(0, MONTHLY_QUOTA - used)}
        )


class EarlyOutreachResubmitView(APIView):
    """POST /api/v1/outreach/requests/{id}/resubmit/ — Story 5.5.

    Student corrects a `rejected` motivation and resubmits it; goes back to
    `pending_moderation`. `get_object_or_404` scopes the lookup to
    `student=request.user` so a student can never resubmit someone else's
    request (would 404, not 403 — doesn't leak that the id exists)."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request: Request, outreach_id: str) -> Response:
        outreach = get_object_or_404(EarlyOutreachRequest, id=outreach_id, student=request.user)
        serializer = EarlyOutreachResubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Not caught here — DomainError subclasses (incl. OutreachModerationStateError)
        # are handled globally by the RFC7807 exception handler.
        outreach = resubmit_early_outreach_motivation(
            outreach=outreach, motivation_text=serializer.validated_data["motivation_text"]
        )
        return Response(EarlyOutreachListSerializer(outreach).data)


class _EcoleOutreachPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class EcoleOutreachQueueView(APIView):
    """GET /api/v1/ecole/outreach/ — Story 5.6 AC (reception queue).

    Filters: `?status=pending|responded|expired_7d`,
    `?ordering=created_at|-created_at` (default `-created_at`, most recent
    first). No compatibility-score sort — no such score exists yet
    anywhere in the codebase (§2 scope decision); adding real
    student↔school matching is out of scope for this story.
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsSchoolAdmin]

    def get(self, request: Request) -> Response:
        school = get_school_for_admin(user=request.user)
        qs = list_school_outreach_requests(
            school=school,
            status=request.query_params.get("status"),
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        paginator = _EcoleOutreachPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = EcoleOutreachListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class EcoleOutreachDetailView(APIView):
    """GET /api/v1/ecole/outreach/{id}/ — Story 5.6 AC (fiche détail).

    404s (not 403) for a request that belongs to another school, or that
    isn't in a receivable status yet (`pending_moderation`/`rejected`) —
    doesn't confirm the id exists at all, matching the resubmit view's
    same choice for the same reason (NFR-S4).
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsSchoolAdmin]

    def get(self, request: Request, outreach_id: str) -> Response:
        school = get_school_for_admin(user=request.user)
        try:
            outreach = get_school_outreach_request(school=school, outreach_id=outreach_id)
        except EarlyOutreachRequest.DoesNotExist as exc:
            raise Http404 from exc
        return Response(EcoleOutreachDetailSerializer(outreach).data)


class EcoleOutreachRespondView(APIView):
    """POST /api/v1/ecole/outreach/{id}/respond/ — Story 5.7 AC.

    Body: `{action, comment?, proposed_slots?}`. 404s the same way the
    detail view does for another school's/not-yet-receivable request;
    `OutreachAlreadyResponded` (409, global RFC7807 handler) if it isn't
    `pending` anymore.
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsSchoolAdmin]

    def post(self, request: Request, outreach_id: str) -> Response:
        school = get_school_for_admin(user=request.user)
        try:
            outreach = get_school_outreach_request(school=school, outreach_id=outreach_id)
        except EarlyOutreachRequest.DoesNotExist as exc:
            raise Http404 from exc

        serializer = EarlyOutreachRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        respond_to_outreach_request(
            outreach=outreach,
            action=serializer.validated_data["action"],
            comment=serializer.validated_data["comment"],
            proposed_slots=serializer.validated_data["proposed_slots"],
        )
        # Re-fetch (not `outreach.refresh_from_db()`) — that would clear the
        # cached `student` FK (loaded under `bypass_rls` inside
        # `get_school_outreach_request`) and force a fresh lookup outside
        # any bypass, which Postgres RLS silently empties for a
        # school-admin session (caught by the Postgres test pass, not
        # SQLite).
        outreach = get_school_outreach_request(school=school, outreach_id=outreach_id)
        return Response(EcoleOutreachDetailSerializer(outreach).data, status=201)


class InterviewAcceptView(APIView):
    """POST /api/v1/outreach/requests/{id}/interview/accept/ — Story 5.7.

    Student accepts one of the school's proposed slots. Scoped to
    `student=request.user` (404, not 403, for someone else's request)."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request: Request, outreach_id: str) -> Response:
        outreach = get_object_or_404(EarlyOutreachRequest, id=outreach_id, student=request.user)
        serializer = InterviewAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        accept_interview_slot(outreach=outreach, slot=serializer.validated_data["slot"])
        outreach.refresh_from_db()
        return Response(EarlyOutreachListSerializer(outreach).data)


class InterviewAlternativeView(APIView):
    """POST /api/v1/outreach/requests/{id}/interview/alternative/ — Story 5.7.

    Student can't make any proposed slot, suggests one instead. Scoped to
    `student=request.user`."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request: Request, outreach_id: str) -> Response:
        outreach = get_object_or_404(EarlyOutreachRequest, id=outreach_id, student=request.user)
        serializer = InterviewAlternativeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        propose_interview_alternative(outreach=outreach, note=serializer.validated_data["note"])
        outreach.refresh_from_db()
        return Response(EarlyOutreachListSerializer(outreach).data)


class EcoleReportingView(APIView):
    """GET /api/v1/ecole/reporting/ — Story 5.10 AC (KPIs).

    Aggregate-only — no student name/email ever appears (the `User` model
    has neither), so RGPD anonymization at the reporting level is
    structural, not a filtering step to remember."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsSchoolAdmin]

    def get(self, request: Request) -> Response:
        school = get_school_for_admin(user=request.user)
        return Response(build_school_reporting(school=school))


class EcoleReportingExportView(APIView):
    """GET /api/v1/ecole/reporting/export.csv/ — Story 5.10 AC (export)."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsSchoolAdmin]

    def get(self, request: Request) -> HttpResponse:
        school = get_school_for_admin(user=request.user)
        csv_content = export_school_reporting_csv(school=school)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="reporting-{school.slug}.csv"'
        return response
