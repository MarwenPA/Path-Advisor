"""URL patterns for early-outreach requests — Story 5.4."""

from django.urls import path

from apps.outreach.views import EarlyOutreachListView, OutreachQuotaView, SchoolOutreachCreateView

app_name = "outreach"

urlpatterns = [
    path("outreach/requests/", EarlyOutreachListView.as_view(), name="request-list"),
    path("outreach/quota/", OutreachQuotaView.as_view(), name="quota"),
    path(
        "schools/<slug:slug>/outreach/",
        SchoolOutreachCreateView.as_view(),
        name="school-outreach-create",
    ),
]
