"""Counselor + student cohort/consent URLs — Story 6.7 (+ 6.6/6.8/6.9).

Mounted at `api/v1/establishments/` in `path_advisor/urls.py` — distinct
from `apps.establishments.urls` (admin-only B2B onboarding, mounted at
`api/v1/admin/`).
"""

from __future__ import annotations

from django.urls import path

from apps.establishments import counselor_views

app_name = "establishments_cohort"

urlpatterns = [
    path(
        "students/<str:student_id>/consent-request/",
        counselor_views.counselor_consent_request,
        name="counselor-consent-request",
    ),
    path(
        "consent-requests/",
        counselor_views.student_pending_consents,
        name="student-pending-consents",
    ),
    path(
        "consent-requests/<str:consent_id>/decide/",
        counselor_views.student_decide_consent,
        name="student-decide-consent",
    ),
    # Story 6.8 — counselor individual profile view
    path(
        "students/<str:student_id>/profile/",
        counselor_views.counselor_student_profile,
        name="counselor-student-profile",
    ),
    path(
        "students/<str:student_id>/notes/",
        counselor_views.counselor_student_notes,
        name="counselor-student-notes",
    ),
    path(
        "students/<str:student_id>/interview-sheet.pdf/",
        counselor_views.counselor_interview_sheet_pdf,
        name="counselor-interview-sheet-pdf",
    ),
]
