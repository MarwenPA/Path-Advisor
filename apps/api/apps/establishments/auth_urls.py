"""Public counselor-invitation URLs — Story 6.5 §T5.1.

Mounted at `api/v1/auth/` in `path_advisor/urls.py` (alongside `apps.accounts.urls`).
"""

from __future__ import annotations

from django.urls import path

from apps.establishments import views

app_name = "establishments_auth"

urlpatterns = [
    path(
        "counselor-invitation/<str:token>/",
        views.counselor_invitation_status,
        name="counselor-invitation-status",
    ),
    path(
        "counselor-invitation/<str:token>/accept/",
        views.counselor_invitation_accept,
        name="counselor-invitation-accept",
    ),
]
