"""
Base Django settings shared across all environments.

Environment-specific files (local.py, staging.py, prod.py, test.py) import from
this module and override what they need.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Security ---
# No placeholder default: every consumer (local/staging/prod/test) MUST set SECRET_KEY.
# If a workflow imports `path_advisor.settings.base` directly and forgets to override,
# Django's deployment checks will refuse to start with a None/empty SECRET_KEY.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS: list[str] = []

# --- Custom user model (Story 1.3) ---
# Must be set BEFORE the first migration runs; switching it after the fact is a
# breaking change. See docs/onboarding.md § Troubleshooting for the reset procedure.
AUTH_USER_MODEL = "accounts.User"
SITE_ID = 1

# --- Applications ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_celery_beat",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    # Story 1.6 — TOTP MFA for staff (mandatory) + B2C (opt-in). Loaded BEFORE
    # `apps.accounts` so the migration graph resolves deterministically.
    # `otp_totp` carries the device + secret + TOTP verification logic;
    # `otp_static` holds the 8 single-use recovery codes per enrolled user.
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.audit",
    "apps.profiles",
    "apps.students",
    # Story 2.3 — bulletin upload + OCR
    "apps.bulletins",
    # Story 3.1 — vocationnel scoring client + recommendations
    "apps.recommendations",
    # Story 3.2 — curated professions referential
    "apps.professions",
    # Story 4.1 — schools & formations referential
    "apps.schools",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Story 1.6 — `OTPMiddleware` sets `request.user.is_verified()` after
    # AuthenticationMiddleware has resolved `request.user`. RBAC code in
    # Story 1.7 will consume `is_verified()` to gate sensitive endpoints
    # behind the MFA challenge. MUST be AFTER `AuthenticationMiddleware`
    # so `request.user` exists, and BEFORE `TenantSessionMiddleware` so
    # the RLS GUC writes see a (possibly) verified user.
    "django_otp.middleware.OTPMiddleware",
    # Story 1.7 §T13 — capture `(actor_id, actor_role, tenant_id, ip_hash,
    # user_agent)` into a thread-local at request start so `@audit_action`
    # decorators (which have no request in their signature) can read it.
    # MUST be AFTER AuthenticationMiddleware + OTPMiddleware so user is
    # resolved + MFA verification status is known.
    "path_advisor.middleware.actor_context.ActorContextMiddleware",
    # Story 1.8: pushes (user_id, tenant_id, role) into PG session GUCs so
    # the RLS policies on `users` / `parental_consents` filter at the DB
    # layer. MUST be AFTER AuthenticationMiddleware (request.user must be
    # resolved) and BEFORE AccountMiddleware (allauth + views run with the
    # GUCs in place).
    "path_advisor.middleware.tenant.TenantSessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # allauth ≥ 0.55 requires its own middleware to inject the request user.
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "path_advisor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Path-Advisor templates take precedence over allauth defaults — without this,
        # allauth's bundled `account/email/*` win because `allauth` is loaded before
        # `apps.accounts` in INSTALLED_APPS.
        "DIRS": [BASE_DIR / "apps" / "accounts" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "path_advisor.wsgi.application"
ASGI_APPLICATION = "path_advisor.asgi.application"

# --- Database (overridden per environment) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "path_advisor"),
        "USER": os.environ.get("POSTGRES_USER", "path_advisor"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "path_advisor_local_dev"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# --- Cache (Redis for rate-limiting, session caching, etc.) ---
# Story 1.3 §9 #3: rate limit storage on Redis (shared across workers, prod-coherent).
# Tests override this to LocMemCache so pytest does not depend on Redis being up.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    }
}

# --- Auth ---
# 12-char minimum (NIST SP 800-63 / Story 1.1 review patch).
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# --- allauth (Story 1.3) ---
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_ADAPTER = "apps.accounts.adapters.PathAdvisorAccountAdapter"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/onboarding"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/auth/verify-email"
# Front (Next.js) builds the verification URL itself, so allauth's URL is only used in tests.
ACCOUNT_RATE_LIMITS = {"login_failed": "5/5m"}

# --- dj-rest-auth (Story 1.3) ---
# Session-based auth only (Story 1.1 decision); we never issue tokens, so dj-rest-auth's
# TokenModel must be explicitly disabled to skip the `rest_framework.authtoken` install.
REST_AUTH = {
    "REGISTER_SERIALIZER": "apps.accounts.serializers.SignupSerializer",
    # Override dj-rest-auth's default UserDetailsSerializer so `/api/v1/auth/user/`
    # exposes the derived `is_fully_active` flag (Story 1.4 §AC3) — the front gates
    # "limited mode" on it without re-implementing the email-verified + active rule.
    "USER_DETAILS_SERIALIZER": "apps.accounts.serializers.UserDetailsSerializer",
    # Story 1.12 — intercepts DELETED-status logins to surface a typed 403 + Problem
    # Details so the front routes to the cancel-flow info page (§AC3).
    "LOGIN_SERIALIZER": "apps.accounts.login_serializer.PathAdvisorLoginSerializer",
    # Story 1.5 — overrides `get_email_options()` to route the password-reset
    # link to the Next.js `/auth/reset-password/<uid>/<token>` page instead
    # of allauth's default Django-served URL.
    "PASSWORD_RESET_SERIALIZER": "apps.accounts.serializers.PathAdvisorPasswordResetSerializer",
    "SESSION_LOGIN": True,
    "USE_JWT": False,
    "TOKEN_MODEL": None,
}

# --- I18n ---
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# --- Static ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "apps.core.exceptions.path_advisor_exception_handler",
    # Per-scope throttle rates. Each scope is set on a ScopedRateThrottle / a
    # custom UserRateThrottle subclass. Story 1.11 adds `gdpr_export_create` as
    # a defense-in-depth layer above the 24h application rate limit.
    "DEFAULT_THROTTLE_RATES": {
        "gdpr_export_create": "50/hour",
    },
}

# --- drf-spectacular ---
# dj-rest-auth's LoginView references its `TokenSerializer` in the success response.
# With TOKEN_MODEL=None (session-cookie auth, ADR-0002), the TokenSerializer is left
# with `model = None` and crashes drf-spectacular introspection. The preprocessing
# hook below drops the offending `/api/v1/auth/token/*` endpoints (we don't expose
# them). Story 1.5's auth endpoints (login, password-reset request/confirm) opt back
# in via explicit `@extend_schema` decorators on the overridden views.
SPECTACULAR_SETTINGS = {
    "TITLE": "Path-Advisor API",
    "DESCRIPTION": "REST API for Path-Advisor — career-orientation platform.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "PREPROCESSING_HOOKS": ["apps.core.openapi.exclude_token_endpoints"],
}

# --- CORS (local dev defaults; tighten per env) ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# --- Session + CSRF (Story 1.3 cross-origin signup) ---
# Secure defaults — `local.py` relaxes them for HTTP dev. Code review §11 patch: defaults
# must be safe; only explicit local-dev overrides allow plain HTTP cookies.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # the front reads the cookie to populate the X-CSRFToken header
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# --- Rate limiting (django-ratelimit, Story 1.3) ---
RATELIMIT_USE_CACHE = "default"

# --- Story 1.5 — Per-account login lockout ---
# Independent from the per-IP throttle on `ThrottledLoginView` (Story 1.12 §D5,
# 5/min/IP). After `LOGIN_FAIL_THRESHOLD` failed attempts within
# `LOGIN_FAIL_WINDOW_SECONDS` for the SAME user, the account is locked for
# `LOGIN_LOCK_DURATION_SECONDS`. Tunable per-env (tests use very low values).
LOGIN_FAIL_THRESHOLD = int(os.environ.get("LOGIN_FAIL_THRESHOLD", 5))
LOGIN_FAIL_WINDOW_SECONDS = int(os.environ.get("LOGIN_FAIL_WINDOW_SECONDS", 900))
LOGIN_LOCK_DURATION_SECONDS = int(os.environ.get("LOGIN_LOCK_DURATION_SECONDS", 600))

# Password-reset token TTL — Django default is 3 days (`PASSWORD_RESET_TIMEOUT`,
# in seconds). Story 1.5 §AC5 mandates 1 hour for tighter security on the
# only credential-recovery surface.
PASSWORD_RESET_TIMEOUT = int(os.environ.get("PASSWORD_RESET_TIMEOUT", 3600))

# --- Story 1.6 — MFA (TOTP) ---
# Issuer string shown in authenticator apps (Google Authenticator, Authy, 1Password)
# next to the account name. Embedded in the `otpauth://` URL the QR code encodes.
OTP_TOTP_ISSUER = "Path-Advisor"
# Short-lived JWT TTL for the `mfa_session` token issued between password-success
# and the MFA challenge. 5 minutes balances QR-scan UX against shoulder-surfing
# of the URL hash from a co-worker's screen. Tests override to a few seconds.
MFA_SESSION_TTL_SECONDS = int(os.environ.get("MFA_SESSION_TTL_SECONDS", 300))
# Number of recovery codes issued at enrollment-confirm. Story 1.6 §AC1 mandates 8.
MFA_RECOVERY_CODES_COUNT = int(os.environ.get("MFA_RECOVERY_CODES_COUNT", 8))
# Threshold (codes remaining) at which the "low-recovery-codes" email triggers.
MFA_RECOVERY_LOW_THRESHOLD = int(os.environ.get("MFA_RECOVERY_LOW_THRESHOLD", 2))

# --- Audit log (Story 1.13) ---
# Salt used to hash client IPs before storing in `audit_logs.ip_address_hash`.
# MUST be set via env in staging/prod (Doppler). Never rotate post-deploy without
# a migration plan — rotating invalidates the ability to correlate past entries.
AUDIT_IP_HASH_SALT = os.environ.get("AUDIT_IP_HASH_SALT", "path-advisor-local-audit-salt")
# CSV exports above this threshold are pushed to S3 via Celery instead of streamed inline.
AUDIT_EXPORT_SYNC_THRESHOLD = 10_000
# Retention horizon for `archive_old_logs` (months). Entries older than this are
# uploaded to S3 but kept in the table — see Story 1.13 §AC6 rationale.
AUDIT_ARCHIVE_AFTER_DAYS = 3 * 365
AUDIT_ARCHIVE_BUCKET = os.environ.get("AUDIT_ARCHIVE_BUCKET", "audit-logs-archive")
# Async CSV exports for the DPO land in a separate bucket from the archives
# (Story 1.13 §4.2 — buckets must NOT be mixed). Stays distinct from
# `bulletins-encrypted` (Story 2.3) too.
AUDIT_EXPORTS_BUCKET = os.environ.get("AUDIT_EXPORTS_BUCKET", "exports-gdpr")
# Presigned URL TTL for async CSV exports (Story 1.13 §AC5 — "lien valable 7 jours").
AUDIT_EXPORT_PRESIGNED_TTL_SECONDS = 7 * 24 * 3600

# --- GDPR portability exports (Story 1.11) ---
# Bucket S3 pour les archives utilisateur (ZIP chiffré). En MVP on partage le bucket avec
# AUDIT_EXPORTS_BUCKET, les préfixes de clé S3 les distinguent (audit-exports/ vs gdpr-exports/).
GDPR_EXPORTS_BUCKET = os.environ.get("GDPR_EXPORTS_BUCKET", AUDIT_EXPORTS_BUCKET)
# TTL du presigned URL servi sur GET /api/v1/me/gdpr-exports/{id}/download. Court car le
# front est authentifié — pas besoin d'un lien réutilisable.
GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS = int(
    os.environ.get("GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS", 300)
)
GDPR_EXPORT_MAX_DOWNLOADS = int(os.environ.get("GDPR_EXPORT_MAX_DOWNLOADS", 10))
GDPR_EXPORT_RATE_LIMIT_HOURS = int(os.environ.get("GDPR_EXPORT_RATE_LIMIT_HOURS", 24))
GDPR_EXPORT_VALIDITY_DAYS = int(os.environ.get("GDPR_EXPORT_VALIDITY_DAYS", 7))
GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS = int(
    os.environ.get("GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS", 25 * 60)
)

# --- GDPR account deletion (Story 1.12 — right to erasure) ---
# Fenêtre de rétractation entre le soft-delete (clic utilisateur) et le hard-delete
# Celery sweep. Le minimum légal raisonnable per la CNIL est ~30 jours pour les
# demandes Article 17. Overridable per-env (tests) via env var.
GDPR_ACCOUNT_DELETION_GRACE_DAYS = int(os.environ.get("GDPR_ACCOUNT_DELETION_GRACE_DAYS", 30))
# Cap d'attempts du hard-delete sweep avant que la row ne soit gelée (intervention DPO).
# 7 = un jour de retry par tentative (le sweep tourne quotidiennement) — au-delà
# c'est un incident infra que le DPO doit traiter manuellement, pas une boucle silencieuse.
GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS = int(
    os.environ.get("GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS", 7)
)
# Préfixes S3 qui hébergent des données utilisateur — listés ici pour que le
# sweep AC6.2 sache quoi purger. Tuple de (bucket_setting_name, prefix_template).
# Chaque future story qui ajoute un bucket par-user (Story 2.3 bulletins, etc.)
# ajoute son tuple ici sans toucher au code du sweep.
GDPR_USER_OWNED_S3_PREFIXES: list[tuple[str, str]] = [
    ("GDPR_EXPORTS_BUCKET", "gdpr-exports/{user_id}/"),
]

# --- Celery ---
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
CELERY_TASK_ALWAYS_EAGER = False

# --- Storage (S3-compatible, MinIO in local) ---
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "http://localhost:9000")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "minio_local")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "minio_local_password")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
# Story 2.3 — encrypted bulletin storage (SSE-S3 at rest, prefix per student)
BULLETINS_BUCKET = os.environ.get("BULLETINS_BUCKET", "bulletins-encrypted")

# --- AI Service (FastAPI scoring microservice) ---
# Story 3.1: Django → ai-service communication via JWT HS256
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")
AI_SERVICE_JWT_SECRET = os.environ.get("AI_SERVICE_JWT_SECRET", "")
AI_SERVICE_JWT_TTL_SECONDS = int(os.environ.get("AI_SERVICE_JWT_TTL_SECONDS", "300"))

# --- Email (overridden per environment) ---
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@path-advisor.local")

# --- Logging (structlog wiring will land in Story 8.1) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
