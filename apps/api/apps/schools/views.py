"""Schools & Formations referential API views — Story 4.1 / 4.2 / 4.3.

Routes (Story 4.1):
  GET /api/v1/admin/schools/                    — admin list (paginated 100/page)
  GET /api/v1/admin/schools/{id}/               — admin detail
  GET /api/v1/admin/formations/                 — admin formations list
  GET /api/v1/schools/{slug}/                   — public school detail (authenticated)
Routes (Story 4.2):
  GET /api/v1/schools/{slug}/admission-stat/    — admission prediction for authenticated user
Routes (Story 4.3):
  GET /api/v1/metiers/{slug}/parcours/          — list parcours for a profession (IsAuthenticated)
"""

from __future__ import annotations

from typing import ClassVar

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsPathAdmin
from apps.professions.models import Profession
from apps.schools.models import Formation, Parcours, School
from apps.schools.serializers import (
    AdmissionStatSerializer,
    FormationAdminSerializer,
    ParcoursSerializer,
    SchoolAdminSerializer,
    SchoolDetailSerializer,
)
from apps.schools.services import AdmissionPredictionService


class _SchoolPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class AdminSchoolViewSet(ReadOnlyModelViewSet):
    """GET /api/v1/admin/schools/ — paginated list + detail, admin only."""

    permission_classes: ClassVar = [IsPathAdmin]
    queryset = School.objects.prefetch_related("formations").order_by("name")
    serializer_class = SchoolAdminSerializer
    pagination_class = _SchoolPagination


class AdminFormationViewSet(ReadOnlyModelViewSet):
    """GET /api/v1/admin/formations/ — paginated list + detail, admin only."""

    permission_classes: ClassVar = [IsPathAdmin]
    queryset = Formation.objects.select_related("school").order_by("name")
    serializer_class = FormationAdminSerializer
    pagination_class = _SchoolPagination


class SchoolDetailView(RetrieveAPIView):
    """GET /api/v1/schools/{slug}/ — full school detail for authenticated users."""

    permission_classes: ClassVar = [IsAuthenticated]
    queryset = School.objects.prefetch_related("formations")
    serializer_class = SchoolDetailSerializer
    lookup_field = "slug"


class AdmissionStatView(APIView):
    """GET /api/v1/schools/{slug}/admission-stat/ — personalised admission prediction.

    Story 4.2 — returns (or computes and persists) the admission probability
    range for the requesting user and the given school.
    """

    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request: Request, slug: str) -> Response:
        school = get_object_or_404(School, slug=slug)
        service = AdmissionPredictionService()
        stat = service.upsert_stat(school=school, user=request.user)
        serializer = AdmissionStatSerializer(stat)
        return Response(serializer.data)


class ParcoursListView(ListAPIView):
    """GET /api/v1/metiers/{slug}/parcours/

    Returns all Parcours for the given profession slug, ordered by is_default DESC
    then niveau_scolaire. Supports optional ?niveau_scolaire= filter.
    Returns 200 + empty list if profession not found (graceful degradation).
    """

    serializer_class = ParcoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        slug = self.kwargs["slug"]

        try:
            profession = Profession.objects.get(slug=slug)
        except Profession.DoesNotExist:
            # Return empty queryset — caller gets 200 [] instead of 404 so the
            # frontend can gracefully display the empty state (AC6).
            return Parcours.objects.none()

        qs = (
            Parcours.objects.filter(profession=profession)
            .select_related("target_school")
            .order_by("-is_default", "niveau_scolaire")
        )

        niveau_scolaire = self.request.query_params.get("niveau_scolaire")
        if niveau_scolaire:
            qs = qs.filter(niveau_scolaire=niveau_scolaire)

        return qs
