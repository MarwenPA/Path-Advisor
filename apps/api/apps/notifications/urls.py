"""Story 8.2 — notification routes (included at `api/v1/`)."""

from django.urls import path

from .views import (
    AdminMilestoneDetailView,
    AdminMilestoneListView,
    DeltaRecapAckView,
    DeltaRecapView,
    NotificationPreferencesView,
    UnsubscribeView,
)

urlpatterns = [
    # Story 9.2 (amendement 8.3) — CRUD visuel du calendrier Parcoursup.
    path(
        "admin/parcoursup-milestones/",
        AdminMilestoneListView.as_view(),
        name="admin-milestones",
    ),
    path(
        "admin/parcoursup-milestones/<int:milestone_id>/",
        AdminMilestoneDetailView.as_view(),
        name="admin-milestone-detail",
    ),
    # Story 8.6 — DeltaRecap "voici ce qui a bougé".
    path("me/delta-recap/", DeltaRecapView.as_view(), name="delta-recap"),
    path("me/delta-recap/ack/", DeltaRecapAckView.as_view(), name="delta-recap-ack"),
    path(
        "me/notification-preferences/",
        NotificationPreferencesView.as_view(),
        name="notification-preferences",
    ),
    path("notifications/unsubscribe/", UnsubscribeView.as_view(), name="notification-unsubscribe"),
]
