"""Schools & Formations referential API views — Story 4.1 / 4.2 / 4.3 / 4.5 / 4.6 / 4.7.

Routes (Story 4.1):
  GET /api/v1/admin/schools/                    — admin list (paginated 100/page)
  GET /api/v1/admin/schools/{id}/               — admin detail
  GET /api/v1/admin/formations/                 — admin formations list
  GET /api/v1/schools/{slug}/                   — public school detail (authenticated)
Routes (Story 4.2):
  GET /api/v1/schools/{slug}/admission-stat/    — admission prediction for authenticated user
Routes (Story 4.3 / 4.5 / 4.6 / 4.7):
  GET /api/v1/metiers/{slug}/parcours/          — parcours list with inline stats, filter metadata, niveau fallback
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


class ParcoursListView(ListAPIView):
    """GET /api/v1/metiers/{slug}/parcours/ — parcours list for a profession.

    Story 4.3: base endpoint returning parcours with nodes/edges.
    Story 4.5: get_serializer_context() passes request so ParcoursSerializer can
    inject personalised admission_stat on each target/ecole node (AC2).
    Story 4.6: serializer includes denormalized target_school filter metadata.
    Story 4.7: adds ?niveau_scolaire= filtering with two-step fallback (AC4):
      1. If ?niveau_scolaire= matches exactly → return those rows.
      2. Else if terminale_generale parcours exist → fall back to them.
      3. Else return all parcours for the profession (graceful degradation).

    Returns 200 + empty list if profession not found.
    Parcours lists are short — pagination is disabled to avoid cursor ordering issues.
    """

    serializer_class = ParcoursSerializer
    permission_classes: ClassVar = [IsAuthenticated]
    # Disable global CursorPagination (ordering='-created' conflicts with our ordering).
    pagination_class = None

    def get_queryset(self):
        slug = self.kwargs["slug"]

        try:
            profession = Profession.objects.get(slug=slug)
        except Profession.DoesNotExist:
            return Parcours.objects.none()

        qs = Parcours.objects.filter(profession=profession).select_related("target_school")

        niveau = self.request.query_params.get("niveau_scolaire", "")
        if niveau:
            exact = qs.filter(niveau_scolaire=niveau)
            if exact.exists():
                return exact.order_by("-is_default", "niveau_scolaire")
            # Fallback to terminale_generale if no exact match
            fallback = qs.filter(niveau_scolaire=Parcours.NiveauScolaire.TERMINALE_GENERALE)
            if fallback.exists():
                return fallback.order_by("-is_default")
            # Last resort: return all
            return qs.order_by("-is_default", "niveau_scolaire")

        return qs.order_by("-is_default", "niveau_scolaire")

    def get_serializer_context(self) -> dict:
        """Inject request so ParcoursSerializer.get_nodes_with_stats can personalise stats."""
        context = super().get_serializer_context()
        # request is already included by GenericAPIView.get_serializer_context,
        # but we document it explicitly for reviewers (Story 4.5 T2).
        return context


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
