"""URL patterns for the Schools & Formations referential — Story 4.1 / 4.2."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.schools.views import (
    AdminFormationViewSet,
    AdminSchoolViewSet,
    AdmissionStatView,
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
]
