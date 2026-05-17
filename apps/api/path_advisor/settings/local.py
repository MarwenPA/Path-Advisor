"""Local development settings."""

import os

from .base import *  # noqa: F403

DEBUG = True

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-for-production")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "api", "0.0.0.0"]

# Email -> Mailpit (SMTP on port 1025 in docker-compose)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "1025"))
EMAIL_USE_TLS = False

# Local dev runs on plain HTTP — relax the Secure-cookie defaults from base.py so the
# browser actually sends them. Staging/prod keep `Secure=True` (inherited from base).
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
