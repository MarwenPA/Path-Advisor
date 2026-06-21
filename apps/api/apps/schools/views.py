"""Schools & Formations referential API views — Story 4.1.

Routes:
  GET /api/v1/admin/schools/       — admin list (paginated 100/page)
  GET /api/v1/admin/schools/{id}/  — admin detail
  GET /api/v1/admin/formations/    — admin formations list
  GET /api/v1/schools/{slug}/      — public school detail (authenticated)
"""

from __future__ import annotations

from typing import ClassVar

from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsPathAdmin
from apps.schools.models import Formation, School
from apps.schools.serializers import (
    FormationAdminSerializer,
    SchoolAdminSerializer,
    SchoolDetailSerializer,
)


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
