"""Profession referential API views — Story 3.2 T3.

Routes:
  GET /api/v1/admin/professions/           — admin list (paginated 50/page)
  GET /api/v1/admin/professions/{slug}/    — admin detail (full fields)
  GET /api/v1/professions/{slug}/          — student public detail (no sources/rome_code)
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsAuthenticatedAndActive, IsPathAdmin, IsStudent
from apps.core.throttling import PublicSeoAnonThrottle
from apps.professions.models import (
    Profession,
    ProfessionReport,
    ProfessionRevision,
    ProfessionStatus,
)
from apps.professions.serializers import (
    ProfessionAdminSerializer,
    ProfessionAdminWriteSerializer,
    ProfessionCatalogSerializer,
    ProfessionPublicSeoSerializer,
    ProfessionPublicSerializer,
    ProfessionReportAdminSerializer,
    ProfessionReportCreateSerializer,
    ProfessionReportResponseSerializer,
    ProfessionRevisionSerializer,
    ProfessionSlugSerializer,
)
from apps.professions.services.referential_admin import (
    archive_profession,
    create_profession,
    rollback_profession,
    update_profession,
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
                subject_id=report.id,
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
    """GET/POST /api/v1/admin/professions/ — Story 9.1 back-office list + create.

    The list covers EVERY editorial status (a draft is invisible everywhere
    else by construction); `q` searches name/slug/sector, `status` filters,
    `sort` accepts name|-name|updated_at|-updated_at.
    """

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    _SORTS = {"name", "-name", "updated_at", "-updated_at"}

    def get(self, request: Request) -> Response:
        qs = Profession.objects.all()
        q = (request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(sector__icontains=q))
        status_filter = request.query_params.get("status")
        if status_filter in ProfessionStatus.values:
            qs = qs.filter(status=status_filter)
        sort = request.query_params.get("sort", "name")
        if sort not in self._SORTS:
            sort = "name"
        qs = qs.order_by(sort)
        paginator = _ProfessionPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ProfessionAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = ProfessionAdminWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profession = create_profession(editor=request.user, data=serializer.validated_data)
        return Response(ProfessionAdminSerializer(profession).data, status=status.HTTP_201_CREATED)


class AdminProfessionDetailView(APIView):
    """GET/PATCH /api/v1/admin/professions/{slug}/ — Story 9.1 (any status)."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def _get(self, slug: str) -> Profession | None:
        return Profession.objects.filter(slug=slug).first()

    def get(self, request: Request, slug: str) -> Response:
        profession = self._get(slug)
        if profession is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProfessionAdminSerializer(profession).data)

    def patch(self, request: Request, slug: str) -> Response:
        profession = self._get(slug)
        if profession is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfessionAdminWriteSerializer(
            instance=profession, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        profession = update_profession(
            profession=profession, editor=request.user, data=serializer.validated_data
        )
        return Response(ProfessionAdminSerializer(profession).data)


class AdminProfessionArchiveView(APIView):
    """POST /api/v1/admin/professions/{slug}/archive/ — the AC's "delete".

    Archiving, never a hard delete: the fiche is referenced by Parcours,
    reports and early-outreach requests (story doc §2.3).
    """

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def post(self, request: Request, slug: str) -> Response:
        profession = Profession.objects.filter(slug=slug).first()
        if profession is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        profession = archive_profession(profession=profession, editor=request.user)
        return Response(ProfessionAdminSerializer(profession).data)


class AdminProfessionRevisionsView(APIView):
    """GET /api/v1/admin/professions/{slug}/revisions/ — history panel."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request, slug: str) -> Response:
        profession = Profession.objects.filter(slug=slug).first()
        if profession is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        revisions = profession.revisions.select_related("editor", "restored_from")[:50]
        return Response({"revisions": ProfessionRevisionSerializer(revisions, many=True).data})


class AdminProfessionRollbackView(APIView):
    """POST /api/v1/admin/professions/{slug}/rollback/{revision_id}/."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def post(self, request: Request, slug: str, revision_id: str) -> Response:
        profession = Profession.objects.filter(slug=slug).first()
        if profession is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        revision = ProfessionRevision.objects.filter(pk=revision_id, profession=profession).first()
        if revision is None:
            return Response({"detail": "Révision inconnue."}, status=status.HTTP_404_NOT_FOUND)
        profession = rollback_profession(
            profession=profession, editor=request.user, revision=revision
        )
        return Response(ProfessionAdminSerializer(profession).data)


class PublicProfessionListView(APIView):
    """GET /api/v1/professions/ — full catalog, paginated (Story 3.13).

    AC-repli: `/accueil`'s "Tes métiers" module links here when the student
    has no scored recommendations yet, so they can browse the whole
    referential rather than see an empty module. Same permission shape as
    the existing detail endpoint (student-only, no anonymous access — this
    is not the SEO-facing public catalog Epic 7 covers, just an
    authenticated repli).
    """

    permission_classes = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request) -> Response:
        qs = Profession.objects.filter(is_active=True).order_by("name")
        paginator = _ProfessionPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ProfessionCatalogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


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
            subject_id=profession.id,
            metadata={"slug": profession.slug},
        )

        serializer = ProfessionPublicSerializer(profession)
        return Response(serializer.data)


class PublicSeoProfessionDetailView(APIView):
    """GET /api/v1/public/professions/{slug}/ — Story 7.1 AC: anonymous SSR
    fiche métier for SEO. `AllowAny` — deliberately unauthenticated so
    Google/Bing (and a logged-out visitor) get a fully-rendered page.

    Distinct from `PublicProfessionDetailView` (misleadingly named —
    despite "Public" it actually requires `IsAuthenticatedAndActive` +
    `IsStudent`, kept as-is/unrenamed to avoid a churny rename across the
    existing authenticated `/metiers/{slug}` flow): this view uses the
    narrower `ProfessionPublicSeoSerializer` and does NOT audit-log at all:
    the GDPR audit trail traces actions on/by identified data subjects, but
    an anonymous view of public referential content has no actor and no
    personal data — a per-hit `record_audit` here was an unbounded,
    unauthenticated DB-write amplifier (DoS + audit-trail pollution) with
    zero traceability value. Traffic analytics belong to the web/CDN access
    logs. Bounded per IP by `PublicSeoAnonThrottle` regardless.
    """

    permission_classes = [AllowAny]
    throttle_classes = [PublicSeoAnonThrottle]

    def get(self, request: Request, slug: str) -> Response:
        try:
            profession = Profession.objects.get(slug=slug, is_active=True)
        except Profession.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfessionPublicSeoSerializer(profession)
        return Response(serializer.data)


class PublicProfessionSlugsView(APIView):
    """GET /api/v1/public/professions/slugs/ — Story 7.4. `AllowAny`.

    Feeds `app/sitemap.ts` — no pagination (the referential is a curated
    catalog, not user-generated content; a few hundred rows tops), no
    heavy fields (just `slug` + `updated_at` for `lastmod`).
    """

    permission_classes = [AllowAny]
    throttle_classes = [PublicSeoAnonThrottle]

    def get(self, request: Request) -> Response:
        professions = Profession.objects.filter(is_active=True).order_by("slug")
        serializer = ProfessionSlugSerializer(professions, many=True)
        return Response(serializer.data)
