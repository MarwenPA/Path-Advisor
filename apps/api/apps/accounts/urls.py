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
]
