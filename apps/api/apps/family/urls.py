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
    # Story 6.2 — parent read-only dashboard
    path(
        "children/",
        views.parent_children_collection,
        name="parent-children-collection",
    ),
    path(
        "children/<str:student_id>/dashboard/",
        views.parent_child_dashboard,
        name="parent-child-dashboard",
    ),
    path(
        "children/<str:student_id>/bulletins/",
        views.parent_child_bulletins_denied,
        name="parent-child-bulletins",
    ),
    # Code review (2026-08) — dedicated parent-scoped detail views (AC2).
    path(
        "children/<str:student_id>/metiers/<slug:slug>/",
        views.parent_child_metier_detail,
        name="parent-child-metier-detail",
    ),
    path(
        "children/<str:student_id>/ecoles/<slug:slug>/",
        views.parent_child_ecole_detail,
        name="parent-child-ecole-detail",
    ),
]
