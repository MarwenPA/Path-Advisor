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

# Story 1.5 §AC10: env-driven `CSRF_TRUSTED_ORIGINS` so production knows the
# real front-end origin (the base.py default ships only localhost values).
# Comma-separated list, e.g. `https://path-advisor.fr,https://app.path-advisor.fr`.
# We REQUIRE this in prod (no fallback) — a wrong-origin login would silently
# fail CSRF and present as a generic 403, which is hard to debug.
# Strip first, THEN check empty-after-strip, so a whitespace-only env var
# (e.g. `CSRF_TRUSTED_ORIGINS=" "`) raises instead of yielding an empty list
# (code-review P17 — Story 1.5 review 2026-05-27).
_csrf_trusted_raw = (os.environ.get("CSRF_TRUSTED_ORIGINS") or "").strip()
if not _csrf_trusted_raw:
    raise ImproperlyConfigured(
        "CSRF_TRUSTED_ORIGINS must be set in production (comma-separated "
        "HTTPS origins of the SPA front-end)."
    )
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_trusted_raw.split(",") if origin.strip()]
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "CSRF_TRUSTED_ORIGINS resolved to an empty list after stripping "
        "(comma-separated env var contained only whitespace)."
    )

# Story 1.5 §AC5: validate `NEXT_PUBLIC_SITE_URL` at startup so a misconfigured
# prod env fails the deploy instead of silently surviving until the first
# password-reset request blows up with `ImproperlyConfigured` (code-review
# P11 — Story 1.5 review 2026-05-27).
_site_url = (os.environ.get("NEXT_PUBLIC_SITE_URL") or "").strip()
if not _site_url:
    raise ImproperlyConfigured(
        "NEXT_PUBLIC_SITE_URL must be set in production — the password-reset "
        "and email-verification flows use it to build the SPA's absolute URL."
    )
if not _site_url.startswith(("http://", "https://")):
    raise ImproperlyConfigured(f"NEXT_PUBLIC_SITE_URL must be an absolute URL (got {_site_url!r}).")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
