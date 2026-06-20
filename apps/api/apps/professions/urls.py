"""URL patterns for the Profession referential — Story 3.2 T3, Story 3.8."""

from django.urls import path

from apps.professions.views import (
    AdminProfessionDetailView,
    AdminProfessionListView,
    ProfessionReportAdminListView,
    ProfessionReportCreateView,
    PublicProfessionDetailView,
)

app_name = "professions"

urlpatterns = [
    # Admin endpoints (IsPathAdmin)
    path("admin/professions/", AdminProfessionListView.as_view(), name="admin-list"),
    path(
        "admin/professions/reports/",
        ProfessionReportAdminListView.as_view(),
        name="admin-reports-list",
    ),
    path(
        "admin/professions/<slug:slug>/", AdminProfessionDetailView.as_view(), name="admin-detail"
    ),
    # Student-facing public endpoints
    path("professions/<slug:slug>/", PublicProfessionDetailView.as_view(), name="public-detail"),
    path(
        "professions/<slug:slug>/reports/",
        ProfessionReportCreateView.as_view(),
        name="report-create",
    ),
]
