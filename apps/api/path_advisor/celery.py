"""Celery application — wired but no tasks registered in this story."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")

app = Celery("path_advisor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
