"""URL patterns for the Profession referential — Story 3.2 T3, Story 3.8."""

from django.urls import path

from apps.professions.views import (
    AdminProfessionDetailView,
    AdminProfessionListView,
    ProfessionReportAdminListView,
    ProfessionReportCreateView,
    PublicProfessionDetailView,
    PublicProfessionListView,
    PublicSeoProfessionDetailView,
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
    path("professions/", PublicProfessionListView.as_view(), name="public-list"),
    path("professions/<slug:slug>/", PublicProfessionDetailView.as_view(), name="public-detail"),
    # Story 7.1 — anonymous SEO fiche métier (AllowAny)
    path(
        "public/professions/<slug:slug>/",
        PublicSeoProfessionDetailView.as_view(),
        name="public-seo-detail",
    ),
    path(
        "professions/<slug:slug>/reports/",
        ProfessionReportCreateView.as_view(),
        name="report-create",
    ),
]
