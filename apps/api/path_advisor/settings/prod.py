"""Production settings."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")

# Story 1.13 — fail loud if the IP-hash salt is left at its base.py default.
# Rotating the salt invalidates past forensic correlation, so we want a
# deliberate value here (Doppler / env), never the public placeholder.
_audit_ip_hash_salt = os.environ.get("AUDIT_IP_HASH_SALT")
if not _audit_ip_hash_salt or _audit_ip_hash_salt == "path-advisor-local-audit-salt":
    raise ImproperlyConfigured(
        "AUDIT_IP_HASH_SALT must be set to a unique secret in production "
        "(Doppler / env). Leaving the placeholder default makes IP hashes "
        "rainbow-table-reversible."
    )
AUDIT_IP_HASH_SALT = _audit_ip_hash_salt

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
