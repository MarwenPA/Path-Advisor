"""Story 8.9 — RUM routes (included at `api/v1/`)."""

from django.urls import path

from .views import RumIngestView, RumSummaryView

urlpatterns = [
    path("rum/vitals/", RumIngestView.as_view(), name="rum-ingest"),
    path("admin/rum/summary/", RumSummaryView.as_view(), name="rum-summary"),
]
