"""Accounts app URLs — endpoints not provided out of the box by dj-rest-auth."""

from __future__ import annotations

from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
]
