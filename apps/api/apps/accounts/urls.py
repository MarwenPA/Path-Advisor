"""Accounts app URLs — endpoints not provided out of the box by dj-rest-auth."""

from __future__ import annotations

from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    # Story 1.4 — parental-consent flow. The `/decide/` rate-limit key uses `post:token`
    # rather than IP because legitimate parents and ISP-NATted teenagers may share an IP.
    path(
        "parental-consent/resend/",
        views.parental_consent_resend,
        name="parental-consent-resend",
    ),
    path(
        "parental-consent/<str:token>/",
        views.parental_consent_status,
        name="parental-consent-status",
    ),
    path(
        "parental-consent/<str:token>/decide/",
        views.parental_consent_decide,
        name="parental-consent-decide",
    ),
    # Story 1.12 — Account deletion (GDPR Article 17). The `/me/...` namespace is for
    # the authenticated user's own request/status; the top-level `account-deletion/<token>/`
    # mounts the public cancel flow (no auth — the token IS the authentication, same
    # contract as the parental-consent landing).
    path(
        "me/account-deletion/",
        views.account_deletion_request,
        name="account-deletion-request",
    ),
    path(
        "me/account-deletion/status/",
        views.account_deletion_status_authenticated,
        name="account-deletion-status-self",
    ),
    path(
        "account-deletion/<str:token>/",
        views.account_deletion_status_public,
        name="account-deletion-status-public",
    ),
    path(
        "account-deletion/<str:token>/cancel/",
        views.account_deletion_cancel,
        name="account-deletion-cancel",
    ),
]
