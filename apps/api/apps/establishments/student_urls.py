"""Public student-import-invitation URLs — Story 6.5 §T5.2.

Mounted at `api/v1/students/` in `path_advisor/urls.py` (alongside `apps.students.urls`
and `apps.bulletins.urls`).
"""

from __future__ import annotations

from django.urls import path

from apps.establishments import views

app_name = "establishments_students"

urlpatterns = [
    path(
        "invitation/<str:token>/",
        views.student_invitation_status,
        name="student-invitation-status",
    ),
    path(
        "invitation/<str:token>/accept/",
        views.student_invitation_accept,
        name="student-invitation-accept",
    ),
]
