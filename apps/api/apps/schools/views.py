"""Schools & Formations referential API views — Story 4.1 / 4.2 / 4.3 / 4.5 / 4.6 / 4.7 / 4.8.

Routes (Story 4.1):
  GET /api/v1/admin/schools/                    — admin list (paginated 100/page)
  GET /api/v1/admin/schools/{id}/               — admin detail
  GET /api/v1/admin/formations/                 — admin formations list
  GET /api/v1/schools/{slug}/                   — public school detail (authenticated)
Routes (Story 4.2):
  GET /api/v1/schools/{slug}/admission-stat/    — admission prediction for authenticated user
Routes (Story 4.3 / 4.5 / 4.6 / 4.7):
  GET /api/v1/metiers/{slug}/parcours/          — parcours list with inline stats, filter metadata, niveau fallback
Routes (Story 4.8):
  POST   /api/v1/schools/{slug}/favorite/       — add school to favorites
  DELETE /api/v1/schools/{slug}/favorite/       — remove school from favorites
  GET    /api/v1/mes-paris/                     — list favorited schools for current user
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.core.permissions import IsPathAdmin
from apps.core.throttling import PublicSeoAnonThrottle
from apps.professions.models import Profession
from apps.schools import referential_admin
from apps.schools.models import (
    AdmissionStat,
    FavoriteSchool,
    Formation,
    Parcours,
    School,
    SchoolRevision,
    SchoolStatus,
)
from apps.schools.serializers import (
    AdmissionStatSerializer,
    FormationAdminSerializer,
    ParcoursPublicSeoSerializer,
    ParcoursSerializer,
    SchoolAdminSerializer,
    SchoolAdminWriteSerializer,
    SchoolCatalogSerializer,
    SchoolDetailSerializer,
    SchoolPublicSeoSerializer,
    SchoolRevisionSerializer,
    SchoolSlugSerializer,
)
from apps.schools.services import AdmissionPredictionService


class _SchoolPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class AdminSchoolViewSet(ModelViewSet):
    """Story 9.2 — back-office CRUD on the schools referential.

    Read-only since 4.x; now the full CRUD, every write routed through
    `referential_admin` (revision snapshot + audit row in the same
    transaction, `status` → `is_active` sync). No `destroy`: the AC's
    "delete" is the `archive` action (a school is referenced by Parcours,
    favourites, admission stats and early-outreach requests).
    """

    permission_classes: ClassVar = [IsPathAdmin]
    queryset = School.objects.prefetch_related("formations").order_by("name")
    serializer_class = SchoolAdminSerializer
    pagination_class = _SchoolPagination
    http_method_names = ["get", "post", "patch", "head", "options"]
    lookup_field = "slug"

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        q = (params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(city__icontains=q))
        if params.get("type") in School.Type.values:
            qs = qs.filter(type=params["type"])
        region = (params.get("region") or "").strip()
        if region:
            qs = qs.filter(region__iexact=region)
        if params.get("status") in SchoolStatus.values:
            qs = qs.filter(status=params["status"])
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return SchoolAdminWriteSerializer
        return SchoolAdminSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = SchoolAdminWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school = referential_admin.create_school(
            editor=request.user, data=serializer.validated_data
        )
        return Response(SchoolAdminSerializer(school).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        school = self.get_object()
        serializer = SchoolAdminWriteSerializer(instance=school, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        school = referential_admin.update_school(
            school=school, editor=request.user, data=serializer.validated_data
        )
        return Response(SchoolAdminSerializer(school).data)

    @action(detail=True, methods=["post"])
    def archive(self, request: Request, slug: str | None = None) -> Response:
        school = referential_admin.archive_school(school=self.get_object(), editor=request.user)
        return Response(SchoolAdminSerializer(school).data)

    @action(detail=True, methods=["get"])
    def revisions(self, request: Request, slug: str | None = None) -> Response:
        rows = self.get_object().revisions.select_related("editor", "restored_from")[:50]
        return Response({"revisions": SchoolRevisionSerializer(rows, many=True).data})

    @action(detail=True, methods=["post"], url_path="rollback/(?P<revision_id>[^/]+)")
    def rollback(
        self, request: Request, slug: str | None = None, revision_id: str | None = None
    ) -> Response:
        school = self.get_object()
        revision = SchoolRevision.objects.filter(pk=str(revision_id), school=school).first()
        if revision is None:
            return Response({"detail": "Révision inconnue."}, status=status.HTTP_404_NOT_FOUND)
        school = referential_admin.rollback_school(
            school=school, editor=request.user, revision=revision
        )
        return Response(SchoolAdminSerializer(school).data)

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request: Request) -> Response:
        """AC import — semicolon CSV, per-line validation, conflicts report.

        Conflicting slugs never overwrite (manual drill-down resolves via
        PATCH); created rows land as DRAFTS in one all-or-nothing
        transaction (a mass import never publishes to students directly).
        """
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"detail": "Fichier CSV manquant (champ « file »)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size > 2 * 1024 * 1024:
            return Response(
                {"detail": "Fichier trop volumineux (max 2 Mo)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            content = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "Encodage invalide — le CSV doit être en UTF-8."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = referential_admin.import_schools_csv(editor=request.user, content=content)
        return Response(report)


class AdminFormationViewSet(ReadOnlyModelViewSet):
    """GET /api/v1/admin/formations/ — paginated list + detail, admin only."""

    permission_classes: ClassVar = [IsPathAdmin]
    queryset = Formation.objects.select_related("school").order_by("name")
    serializer_class = FormationAdminSerializer
    pagination_class = _SchoolPagination


class SchoolListView(ListAPIView):
    """GET /api/v1/schools/ — full catalog, paginated (mirrors Story 3.13's
    profession catalog). `/accueil`'s "Tes paris" module links here so a
    student/parent can browse the whole schools referential, not just their
    own favorites (`/mes-paris`, unchanged).
    """

    permission_classes: ClassVar = [IsAuthenticated]
    # Deactivated schools are hidden from the browsable catalog (mirrors the
    # profession catalog's is_active filter); existing favorites pointing at a
    # deactivated school stay reachable via /mes-paris and /schools/{slug}.
    queryset = School.objects.filter(is_active=True).order_by("name")
    serializer_class = SchoolCatalogSerializer
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


class SchoolPublicSeoDetailView(RetrieveAPIView):
    """GET /api/v1/public/schools/{slug}/ — Story 7.2 AC: anonymous SSR
    fiche école/formation for SEO. `AllowAny` — no `admission_stat`
    (`SchoolPublicSeoSerializer`), so `<FicheEcole>` naturally skips the
    personalized `<AdmissionStatPoller>` (it's conditional on that field
    being present) rather than needing a separate anonymous variant.
    Deactivated schools 404 here — they must never be served to anonymous
    visitors (mirrors the `is_active=True` filter on every public
    profession endpoint).
    """

    permission_classes: ClassVar = [AllowAny]
    throttle_classes = [PublicSeoAnonThrottle]
    queryset = School.objects.filter(is_active=True).prefetch_related("formations")
    serializer_class = SchoolPublicSeoSerializer
    lookup_field = "slug"


class SchoolPublicSlugsView(ListAPIView):
    """GET /api/v1/public/schools/slugs/ — Story 7.4. Feeds `app/sitemap.ts`
    (mirrors `PublicProfessionSlugsView`, including its `is_active` filter —
    a deactivated school must not be sitemapped)."""

    permission_classes: ClassVar = [AllowAny]
    throttle_classes = [PublicSeoAnonThrottle]
    queryset = School.objects.filter(is_active=True).order_by("slug")
    serializer_class = SchoolSlugSerializer
    pagination_class = None


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


class ParcoursPublicSeoListView(ListAPIView):
    """GET /api/v1/public/metiers/{slug}/parcours/ — Story 7.3 AC. `AllowAny`
    — feeds the "Quels bacs / formations choisir ?" panel + "écoles cibles"
    links on the long-tail SEO landing pages. Uses the narrower
    `ParcoursPublicSeoSerializer` (no nodes/edges graph, no personalized
    admission_stat).

    Unlike `ParcoursListView` (whose terminale_generale fallback is an
    in-app UX affordance — Story 4.7 AC4, the student sees which niveau is
    shown), this endpoint returns an EMPTY list when the requested
    `niveau_scolaire` has no rows: the SEO pages render the result under a
    niveau-specific heading, so silently substituting another niveau would
    publish factually wrong content (e.g. post-bac formations presented as
    3ème options). The frontend already has a proper empty state.

    Parcours whose `target_school` has been deactivated are excluded
    (rows without a target_school are kept — nothing to leak).
    """

    serializer_class = ParcoursPublicSeoSerializer
    permission_classes: ClassVar = [AllowAny]
    throttle_classes = [PublicSeoAnonThrottle]
    pagination_class = None

    def get_queryset(self):
        slug = self.kwargs["slug"]
        try:
            profession = Profession.objects.get(slug=slug, is_active=True)
        except Profession.DoesNotExist:
            return Parcours.objects.none()

        qs = (
            Parcours.objects.filter(profession=profession)
            .exclude(target_school__is_active=False)
            .select_related("target_school")
        )

        niveau = self.request.query_params.get("niveau_scolaire", "")
        if niveau:
            # No fallback on the public path — exact niveau match or nothing.
            qs = qs.filter(niveau_scolaire=niveau)

        return qs.order_by("-is_default", "niveau_scolaire")


class AdmissionStatView(APIView):
    """GET /api/v1/schools/{slug}/admission-stat/ — personalised admission prediction.

    Story 4.2 — returns (or computes and persists) the admission probability
    range for the requesting user and the given school.

    Story 5.8 — skips the usual bulletin-based recompute (`upsert_stat`,
    which unconditionally overwrites `expected_proba`) when a school's
    early-outreach response nudged the stat within the last 24h
    (`outreach_delta_applied_at`). Without this guard, a student checking
    their fiche école moments after the "l'école a répondu" notification —
    the exact moment they're most likely to look — would immediately have
    the "+15 pts" badge silently erased by a same-poll recompute.
    """

    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request: Request, slug: str) -> Response:
        # Story 7.10 (Part B) AC4: no prediction for a deactivated school — a
        # probability against a school removed from the referential is
        # meaningless, and recomputing here would also persist a fresh stat
        # row for it. The fiche itself stays reachable (SchoolDetailView is
        # deliberately unfiltered); only the prediction endpoint 404s.
        school = get_object_or_404(School, slug=slug, is_active=True)
        service = AdmissionPredictionService()

        existing = AdmissionStat.objects.filter(school=school, user=request.user).first()
        if existing and existing.outreach_delta_applied_at:
            recent = (timezone.now() - existing.outreach_delta_applied_at) < timedelta(hours=24)
            if recent:
                return Response(AdmissionStatSerializer(existing).data)

        stat = service.upsert_stat(school=school, user=request.user)
        serializer = AdmissionStatSerializer(stat)
        return Response(serializer.data)


class SchoolFavoriteView(APIView):
    """POST/DELETE /api/v1/schools/{slug}/favorite/ — toggle school favorite.

    Story 4.8:
      POST   → get_or_create FavoriteSchool row, return 201 {"favorited": true}.
      DELETE → delete FavoriteSchool row if exists, return 200 {"favorited": false}.
    """

    permission_classes: ClassVar = [IsAuthenticated]

    def post(self, request: Request, slug: str) -> Response:
        school = get_object_or_404(School, slug=slug)
        FavoriteSchool.objects.get_or_create(user=request.user, school=school)
        return Response({"favorited": True}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, slug: str) -> Response:
        school = get_object_or_404(School, slug=slug)
        FavoriteSchool.objects.filter(user=request.user, school=school).delete()
        return Response({"favorited": False}, status=status.HTTP_200_OK)


class MesParisListView(ListAPIView):
    """GET /api/v1/mes-paris/ — list schools favorited by the authenticated user.

    Story 4.8: returns School objects (SchoolDetailSerializer) ordered by most
    recently added to favorites.
    """

    permission_classes: ClassVar = [IsAuthenticated]
    serializer_class = SchoolDetailSerializer
    pagination_class = None  # Client consumes the full list at once

    def get_queryset(self):
        return (
            School.objects.filter(favorited_by__user=self.request.user)
            .prefetch_related("formations", "admission_stats")
            .order_by("-favorited_by__created_at")
        )
