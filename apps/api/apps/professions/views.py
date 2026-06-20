"""Profession referential API views — Story 3.2 T3.

Routes:
  GET /api/v1/admin/professions/           — admin list (paginated 50/page)
  GET /api/v1/admin/professions/{slug}/    — admin detail (full fields)
  GET /api/v1/professions/{slug}/          — student public detail (no sources/rome_code)
"""

from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsAuthenticatedAndActive, IsPathAdmin, IsStudent
from apps.professions.models import Profession, ProfessionReport
from apps.professions.serializers import (
    ProfessionAdminSerializer,
    ProfessionPublicSerializer,
    ProfessionReportAdminSerializer,
    ProfessionReportCreateSerializer,
    ProfessionReportResponseSerializer,
)


class _ProfessionPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class ProfessionReportCreateView(APIView):
    """POST /api/v1/professions/{slug}/reports/ — student creates an error report (AC4)."""

    permission_classes = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request: Request, slug: str) -> Response:
        try:
            profession = Profession.objects.get(slug=slug, is_active=True)
        except Profession.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfessionReportCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            report = ProfessionReport.objects.create(
                profession=profession,
                reporter=request.user,
                **serializer.validated_data,
            )

            record_audit(
                action="profession_report_created",
                result=AuditResult.SUCCESS,
                actor=request.user,
                subject=report,
                metadata={
                    "profession_slug": profession.slug,
                    "error_type": report.error_type,
                    "reporter_id": str(request.user.pk),
                    "report_id": report.id,
                },
            )

        return Response(
            ProfessionReportResponseSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class ProfessionReportAdminListView(APIView):
    """GET /api/v1/admin/professions/reports/ — paginated list for admin (AC6)."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request) -> Response:
        qs = ProfessionReport.objects.filter(status="pending").select_related(
            "profession", "reporter"
        )
        paginator = _ProfessionPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ProfessionReportAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminProfessionListView(APIView):
    """GET /api/v1/admin/professions/ — paginated list, admin only."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request) -> Response:
        qs = Profession.objects.filter(is_active=True).order_by("name")
        paginator = _ProfessionPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ProfessionAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminProfessionDetailView(APIView):
    """GET /api/v1/admin/professions/{slug}/ — full detail, admin only."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request, slug: str) -> Response:
        try:
            profession = Profession.objects.get(slug=slug, is_active=True)
        except Profession.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfessionAdminSerializer(profession)
        return Response(serializer.data)


class PublicProfessionDetailView(APIView):
    """GET /api/v1/professions/{slug}/ — public fields for authenticated students.

    Audit logs a `profession_viewed` event per Story 1.13.
    """

    permission_classes = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request, slug: str) -> Response:
        try:
            profession = Profession.objects.get(slug=slug, is_active=True)
        except Profession.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        record_audit(
            action="profession_viewed",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject=profession,
            metadata={"slug": profession.slug},
        )

        serializer = ProfessionPublicSerializer(profession)
        return Response(serializer.data)
