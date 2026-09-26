"""Story 8.2 — notification routes (included at `api/v1/`)."""

from django.urls import path

from .views import NotificationPreferencesView, UnsubscribeView

urlpatterns = [
    path(
        "me/notification-preferences/",
        NotificationPreferencesView.as_view(),
        name="notification-preferences",
    ),
    path("notifications/unsubscribe/", UnsubscribeView.as_view(), name="notification-unsubscribe"),
]
