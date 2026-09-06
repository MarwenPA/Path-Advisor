from __future__ import annotations

from django.apps import AppConfig


class OutreachConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.outreach"
    label = "outreach"
    verbose_name = "Envoi anticipé (Premium B2C)"
