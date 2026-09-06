"""URL patterns for the Schools & Formations referential — Story 4.1 / 4.2 / 4.3 / 4.5 / 4.6 / 4.7 / 4.8."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.schools.views import (
    AdminFormationViewSet,
    AdminSchoolViewSet,
    AdmissionStatView,
    MesParisListView,
    ParcoursListView,
    ParcoursPublicSeoListView,
    SchoolDetailView,
    SchoolFavoriteView,
    SchoolListView,
    SchoolPublicSeoDetailView,
    SchoolPublicSlugsView,
)

app_name = "schools"

admin_router = DefaultRouter()
admin_router.register("schools", AdminSchoolViewSet, basename="admin-school")
admin_router.register("formations", AdminFormationViewSet, basename="admin-formation")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("schools/", SchoolListView.as_view(), name="school-list"),
    path("schools/<slug:slug>/", SchoolDetailView.as_view(), name="school-detail"),
    # Story 7.4 — sitemap slugs feed (AllowAny). MUST precede the
    # <slug:slug> pattern below.
    path(
        "public/schools/slugs/",
        SchoolPublicSlugsView.as_view(),
        name="public-school-slugs",
    ),
    # Story 7.2 — anonymous SEO fiche école/formation (AllowAny)
    path(
        "public/schools/<slug:slug>/",
        SchoolPublicSeoDetailView.as_view(),
        name="public-seo-school-detail",
    ),
    path(
        "schools/<slug:slug>/admission-stat/",
        AdmissionStatView.as_view(),
        name="school-admission-stat",
    ),
    # Story 4.8 — favorite toggle + mes paris list
    path(
        "schools/<slug:slug>/favorite/",
        SchoolFavoriteView.as_view(),
        name="school-favorite",
    ),
    path(
        "mes-paris/",
        MesParisListView.as_view(),
        name="mes-paris",
    ),
    # Story 4.3 / 4.5 / 4.6 / 4.7 — parcours list for a given metier with inline stats, filter metadata, niveau fallback
    path(
        "metiers/<slug:slug>/parcours/",
        ParcoursListView.as_view(),
        name="metier-parcours-list",
    ),
    # Story 7.3 — anonymous SEO parcours summary (AllowAny)
    path(
        "public/metiers/<slug:slug>/parcours/",
        ParcoursPublicSeoListView.as_view(),
        name="public-seo-metier-parcours-list",
    ),
]
