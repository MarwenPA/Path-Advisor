from __future__ import annotations

from django.apps import AppConfig


class EstablishmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.establishments"
    label = "establishments"
    verbose_name = "Établissements B2B"
