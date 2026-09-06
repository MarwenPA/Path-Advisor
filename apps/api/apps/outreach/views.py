"""Early-outreach API views — Stories 5.4 + 5.5.

Routes:
  POST /api/v1/schools/{slug}/outreach/       — create a request for that school (AC2/AC3/AC5)
  GET  /api/v1/outreach/requests/             — list current user's requests (AC4)
  GET  /api/v1/outreach/quota/                — current-month quota status (AC1/AC3)
  POST /api/v1/outreach/requests/{id}/resubmit/ — student corrects+resubmits a rejected motivation (5.5)

Moderation itself (approve/reject a `pending_moderation` motivation) is a
`path_admin` action exposed via the Django admin (`apps/outreach/admin.py`),
not a separate DRF endpoint — Story 9.4 (back-office admin) is the future
home for a dedicated moderation queue UI; the admin is the interim tool.
"""

from __future__ import annotations

from typing import ClassVar

from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services.subscription_service import SubscriptionService
from apps.core.permissions import IsAuthenticatedAndActive, IsStudent
from apps.outreach.models import EarlyOutreachRequest
from apps.outreach.serializers import (
    EarlyOutreachCreateSerializer,
    EarlyOutreachListSerializer,
    EarlyOutreachResubmitSerializer,
)
from apps.outreach.services.early_outreach import (
    MONTHLY_QUOTA,
    count_outreach_this_month,
    create_early_outreach_request,
    resubmit_early_outreach_motivation,
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
            "school", "profession"
        )
        paginator = _OutreachPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = EarlyOutreachListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


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
