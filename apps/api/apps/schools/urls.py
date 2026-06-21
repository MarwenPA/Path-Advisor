"""URL patterns for the Schools & Formations referential — Story 4.1 / 4.2 / 4.7."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.schools.views import (
    AdminFormationViewSet,
    AdminSchoolViewSet,
    AdmissionStatView,
    ParcoursListView,
    SchoolDetailView,
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
    # Story 4.7 — parcours list per profession
    path(
        "metiers/<slug:slug>/parcours/",
        ParcoursListView.as_view(),
        name="metier-parcours-list",
    ),
]
