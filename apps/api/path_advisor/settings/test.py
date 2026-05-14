"""Test settings — in-memory SQLite for fast unit tests; PostgreSQL fixture-based tests run separately."""

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key-not-secret"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
