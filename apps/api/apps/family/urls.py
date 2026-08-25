"""Family app URLs — Story 6.1."""

from __future__ import annotations

from django.urls import path

from apps.family import views

app_name = "family"

urlpatterns = [
    path(
        "parent-invitations/",
        views.parent_invitations_collection,
        name="parent-invitation-collection",
    ),
    path(
        "parent-invitations/<str:invitation_id>/resend/",
        views.parent_invitation_resend,
        name="parent-invitation-resend",
    ),
    path(
        "parent-invitations/<str:token>/",
        views.parent_invitation_status,
        name="parent-invitation-status",
    ),
    path(
        "parent-invitations/<str:token>/accept/",
        views.parent_invitation_accept,
        name="parent-invitation-accept",
    ),
]
