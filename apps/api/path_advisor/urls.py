"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.accounts.views import ThrottledRegisterView, ThrottledResendEmailView

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
