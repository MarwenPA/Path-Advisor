"""Test settings — in-memory SQLite for fast unit tests; PostgreSQL fixture-based tests run separately."""

import os

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

# In-process cache so pytest does not need Redis. Rate-limit counters reset every test.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "path-advisor-tests",
    }
}

# The locmem cache above is process-wide, so anonymous-throttle counters would
# accumulate across the whole suite (every APIClient shares one test IP). Raise
# the public SEO rate so unrelated tests never trip it — the dedicated throttle
# test pins a low rate on the class itself.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "gdpr_export_create": "50/hour",
    "public_seo": "100000/min",
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True

# Pin a deterministic host so the email-confirmation URL is stable across runs and so
# the adapter's `ImproperlyConfigured` fail-fast (non-DEBUG path) does not trip in tests.
os.environ.setdefault("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")

# AI Service test config — no real HTTP calls in unit tests (mocked via unittest.mock)
AI_SERVICE_URL = "http://ai-service-test:8001"
AI_SERVICE_JWT_SECRET = "test-ai-jwt-secret-min-32-chars-for-hmac!!"
AI_SERVICE_JWT_TTL_SECONDS = 300
