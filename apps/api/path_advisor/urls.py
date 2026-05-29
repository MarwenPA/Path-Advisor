"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.accounts.views import (
    ThrottledLoginView,
    ThrottledPasswordResetConfirmView,
    ThrottledPasswordResetView,
    ThrottledRegisterView,
    ThrottledResendEmailView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Path-Advisor-specific auth endpoints (csrf bootstrap, etc.) come first so they take
    # precedence over the generic dj_rest_auth include below.
    path("api/v1/auth/", include("apps.accounts.urls")),
    # Override dj-rest-auth registration + resend-email with our rate-limited variants
    # (cf. code review §11 — resend-email was previously unthrottled and abuse-prone).
    path("api/v1/auth/registration/", ThrottledRegisterView.as_view(), name="rest_register"),
    path(
        "api/v1/auth/registration/resend-email/",
        ThrottledResendEmailView.as_view(),
        name="rest_resend_email",
    ),
    # Story 1.12 — override the default login endpoint with a per-IP throttle
    # to cap enumeration via the DELETED-state 403 leak. Must come BEFORE the
    # dj_rest_auth.urls include below so `name="rest_login"` resolves here.
    # Story 1.5 §T11 — `re_path` with `/?$` matches both `/auth/login/` AND
    # `/auth/login` so dj_rest_auth's no-slash variant (loaded via include
    # below) doesn't shadow our throttled subclass on slash-less requests.
    # The `reverse('rest_login')` resolution still wins for us because the
    # last-registered name wins and we re-declare it on the include below.
    re_path(
        r"^api/v1/auth/login/?$",
        ThrottledLoginView.as_view(),
        name="rest_login",
    ),
    # Story 1.5 — throttled password-reset endpoints. Same `re_path` shape so
    # both trailing-slash variants land on our throttled subclasses (audit
    # logging + per-email throttle + Next.js URL via
    # PathAdvisorPasswordResetSerializer).
    re_path(
        r"^api/v1/auth/password/reset/?$",
        ThrottledPasswordResetView.as_view(),
        name="rest_password_reset",
    ),
    re_path(
        r"^api/v1/auth/password/reset/confirm/?$",
        ThrottledPasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    path("api/v1/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/v1/auth/", include("dj_rest_auth.urls")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    # Story 1.11 — GDPR Article 20 exports (POST/GET /api/v1/me/gdpr-exports[/{id}[/download]]).
    path("api/v1/me/", include("apps.accounts.gdpr_urls")),
    # OpenAPI / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
