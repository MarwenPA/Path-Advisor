"""Schools & Formations referential API views — Story 4.1 / 4.2.

Routes:
  GET /api/v1/admin/schools/                    — admin list (paginated 100/page)
  GET /api/v1/admin/schools/{id}/               — admin detail
  GET /api/v1/admin/formations/                 — admin formations list
  GET /api/v1/schools/{slug}/                   — public school detail (authenticated)
  GET /api/v1/schools/{slug}/admission-stat/    — admission prediction for authenticated user
"""

from __future__ import annotations

from typing import ClassVar

from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsPathAdmin
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
    """GET /api/v1/schools/{slug}/ — full school detail for authenticated users.

    Story 4.5: queryset prefetches admission_stats so get_admission_stat avoids N+1.
    formation_id is injected into serializer context for future use (Story 4.5 T1).
    """

    permission_classes: ClassVar = [IsAuthenticated]
    queryset = School.objects.prefetch_related("formations", "admission_stats")
    serializer_class = SchoolDetailSerializer
    lookup_field = "slug"

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context["formation_id"] = self.request.query_params.get("formation_id")
        return context


class ParcoursListView(APIView):
    """GET /api/v1/metiers/{slug}/parcours/ — list of Parcours for a profession.

    Story 4.5: passes request to serializer context so ParcoursSerializer can
    enrich nodes with personalised admission_stat inline (AC2).
    """

    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request: Request, slug: str) -> Response:
        from apps.professions.models import Profession

        profession = get_object_or_404(Profession, slug=slug, is_active=True)
        queryset = Parcours.objects.filter(profession=profession)
        serializer = ParcoursSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


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
