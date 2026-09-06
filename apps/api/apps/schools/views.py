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

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsPathAdmin
from apps.core.throttling import PublicSeoAnonThrottle
from apps.professions.models import Profession
from apps.schools.models import AdmissionStat, FavoriteSchool, Formation, Parcours, School
from apps.schools.serializers import (
    AdmissionStatSerializer,
    FormationAdminSerializer,
    ParcoursPublicSeoSerializer,
    ParcoursSerializer,
    SchoolAdminSerializer,
    SchoolCatalogSerializer,
    SchoolDetailSerializer,
    SchoolPublicSeoSerializer,
    SchoolSlugSerializer,
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
        school = get_object_or_404(School, slug=slug)
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
