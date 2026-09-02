"""Admin (write) URLs for the establishments app — Story 6.5 §T4.

Mounted at `api/v1/admin/` in `path_advisor/urls.py`.
"""

from __future__ import annotations

from django.urls import path

from apps.establishments import views

app_name = "establishments"

urlpatterns = [
    path(
        "establishments/",
        views.EstablishmentListCreateView.as_view(),
        name="establishment-list-create",
    ),
    path(
        "establishments/<uuid:establishment_id>/cohorts/",
        views.EstablishmentCohortListCreateView.as_view(),
        name="establishment-cohort-list-create",
    ),
    path(
        "establishments/<uuid:establishment_id>/counselors/",
        views.EstablishmentCounselorListCreateView.as_view(),
        name="establishment-counselor-list-create",
    ),
    path(
        "cohorts/<str:cohort_id>/import-csv/",
        views.CohortImportCsvView.as_view(),
        name="cohort-import-csv",
    ),
    path(
        "cohorts/<str:cohort_id>/import-jobs/<str:job_id>/",
        views.CohortImportJobDetailView.as_view(),
        name="cohort-import-job-detail",
    ),
]
