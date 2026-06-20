"""Story 2.6 — GET /me/profile (aggregated), POST /me/profile/recompute,
GET /me/profile/history, POST /me/profile/history/snapshot.
"""

from __future__ import annotations

from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from rest_framework.views import APIView

from .models import StudentProfile, StudentProfileHistory
from .views_bulletins_status import _get_or_create_profile


class ProfileAggregatedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        profile = _get_or_create_profile(request.user)
        level_profile = getattr(profile, "level_profile", None)
        data = {
            "id": profile.id,
            "passions": profile.passions,
            "valeurs": profile.valeurs,
            "interets": profile.interets,
            "onboarding_step1_status": profile.onboarding_step1_status,
            "bulletins_status": profile.bulletins_status,
            "bulletins_postponed_at": profile.bulletins_postponed_at,
            "bulletins_postponed_banner_dismissed_until": profile.bulletins_postponed_banner_dismissed_until,
            "level": level_profile.level if level_profile else None,
            "filiere": level_profile.filiere if level_profile else None,
            "specialites": level_profile.specialites if level_profile else [],
            "sous_filiere_techno": level_profile.sous_filiere_techno if level_profile else None,
            "updated_at": profile.updated_at,
        }
        return Response(data)


class ProfileRecomputeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        _get_or_create_profile(request.user)
        # Celery worker stub — Epic 3 will wire the real task.
        return Response({"detail": "recompute_queued"}, status=HTTP_202_ACCEPTED)


class _HistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProfileHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        profile = _get_or_create_profile(request.user)
        qs = StudentProfileHistory.objects.filter(student=profile)
        paginator = _HistoryPagination()
        page = paginator.paginate_queryset(qs, request) or []
        items = [
            {
                "id": h.id,
                "archived_reason": h.archived_reason,
                "previous_state": h.previous_state,
                "created_at": h.created_at,
            }
            for h in page
        ]
        return paginator.get_paginated_response(items)


class ProfileHistorySnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        profile = _get_or_create_profile(request.user)
        archived_reason = request.data.get("archived_reason", "")
        previous_state = request.data.get("previous_state", {})
        entry = StudentProfileHistory.objects.create(
            student=profile,
            archived_reason=archived_reason,
            previous_state=previous_state,
        )
        return Response(
            {
                "id": entry.id,
                "archived_reason": entry.archived_reason,
                "previous_state": entry.previous_state,
                "created_at": entry.created_at,
            },
            status=HTTP_201_CREATED,
        )
