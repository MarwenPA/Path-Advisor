"""URL patterns for early-outreach requests — Stories 5.4 + 5.5 + 5.6 + 5.7 + 5.9 + 5.10."""

from django.urls import path

from apps.outreach.views import (
    EarlyOutreachDetailView,
    EarlyOutreachListView,
    EarlyOutreachResubmitView,
    EcoleOutreachDetailView,
    EcoleOutreachQueueView,
    EcoleOutreachRespondView,
    EcoleReportingExportView,
    EcoleReportingView,
    InterviewAcceptView,
    InterviewAlternativeView,
    OutreachQuotaView,
    SchoolOutreachCreateView,
)

app_name = "outreach"

urlpatterns = [
    path("outreach/requests/", EarlyOutreachListView.as_view(), name="request-list"),
    path("outreach/quota/", OutreachQuotaView.as_view(), name="quota"),
    path(
        "outreach/requests/<str:outreach_id>/",
        EarlyOutreachDetailView.as_view(),
        name="request-detail",
    ),
    path(
        "outreach/requests/<str:outreach_id>/resubmit/",
        EarlyOutreachResubmitView.as_view(),
        name="request-resubmit",
    ),
    path(
        "outreach/requests/<str:outreach_id>/interview/accept/",
        InterviewAcceptView.as_view(),
        name="interview-accept",
    ),
    path(
        "outreach/requests/<str:outreach_id>/interview/alternative/",
        InterviewAlternativeView.as_view(),
        name="interview-alternative",
    ),
    path(
        "schools/<slug:slug>/outreach/",
        SchoolOutreachCreateView.as_view(),
        name="school-outreach-create",
    ),
    path("ecole/outreach/", EcoleOutreachQueueView.as_view(), name="ecole-outreach-queue"),
    path(
        "ecole/outreach/<str:outreach_id>/",
        EcoleOutreachDetailView.as_view(),
        name="ecole-outreach-detail",
    ),
    path(
        "ecole/outreach/<str:outreach_id>/respond/",
        EcoleOutreachRespondView.as_view(),
        name="ecole-outreach-respond",
    ),
    path("ecole/reporting/", EcoleReportingView.as_view(), name="ecole-reporting"),
    path(
        "ecole/reporting/export.csv/",
        EcoleReportingExportView.as_view(),
        name="ecole-reporting-export",
    ),
]
