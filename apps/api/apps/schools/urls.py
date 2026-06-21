"""URL patterns for the Schools & Formations referential — Story 4.1 / 4.2 / 4.3 / 4.5 / 4.6 / 4.7 / 4.8."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.schools.views import (
    AdminFormationViewSet,
    AdminSchoolViewSet,
    AdmissionStatView,
    MesParisListView,
    ParcoursListView,
    SchoolDetailView,
    SchoolFavoriteView,
)

app_name = "schools"

admin_router = DefaultRouter()
admin_router.register("schools", AdminSchoolViewSet, basename="admin-school")
admin_router.register("formations", AdminFormationViewSet, basename="admin-formation")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("schools/<slug:slug>/", SchoolDetailView.as_view(), name="school-detail"),
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
]
