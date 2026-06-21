"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path, re_path
from django_ratelimit.decorators import ratelimit
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
    mfa_challenge_view,
    mfa_disable_view,
    mfa_enroll_confirm_view,
    mfa_enroll_start_from_session_view,
    mfa_enroll_start_view,
    mfa_regenerate_recovery_codes_view,
)

# Rate-limit wrappers applied at URL-wire time so the per-IP / per-user caps
# documented in Story 1.6 §T5 land on the right endpoints. Using `block=False`
# keeps the upstream `request.limited` pattern Story 1.5's views already check
# via `RateLimited` — the MFA views consume `request.limited` the same way.
_mfa_enroll_start = ratelimit(key="ip", rate="5/h", block=False)(mfa_enroll_start_view)
_mfa_enroll_start_from_session = ratelimit(key="user_or_ip", rate="3/h", block=False)(
    mfa_enroll_start_from_session_view
)
_mfa_enroll_confirm = ratelimit(key="ip", rate="10/h", block=False)(mfa_enroll_confirm_view)
_mfa_challenge = ratelimit(key="ip", rate="5/h", block=False)(mfa_challenge_view)
_mfa_disable = ratelimit(key="user_or_ip", rate="3/h", block=False)(mfa_disable_view)
_mfa_regenerate = ratelimit(key="user_or_ip", rate="5/h", block=False)(
    mfa_regenerate_recovery_codes_view
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
    # Story 1.6 — MFA endpoints (TOTP). Five public + auth-required surfaces.
    # All declared with `re_path` slash-tolerant pattern matching Story 1.5's
    # convention so a missing trailing slash doesn't fall through to a 404.
    re_path(r"^api/v1/auth/mfa/enroll/start/?$", _mfa_enroll_start, name="mfa_enroll_start"),
    # Story 1.6 code-review D3 — in-place enrollment for B2C users opting
    # into MFA from `/parametres/securite/mfa` (no need to logout/login).
    re_path(
        r"^api/v1/auth/mfa/enroll/start-from-session/?$",
        _mfa_enroll_start_from_session,
        name="mfa_enroll_start_from_session",
    ),
    re_path(
        r"^api/v1/auth/mfa/enroll/confirm/?$",
        _mfa_enroll_confirm,
        name="mfa_enroll_confirm",
    ),
    re_path(r"^api/v1/auth/mfa/challenge/?$", _mfa_challenge, name="mfa_challenge"),
    re_path(r"^api/v1/auth/mfa/disable/?$", _mfa_disable, name="mfa_disable"),
    re_path(
        r"^api/v1/auth/mfa/recovery-codes/regenerate/?$",
        _mfa_regenerate,
        name="mfa_regenerate_recovery_codes",
    ),
    path("api/v1/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/v1/auth/", include("dj_rest_auth.urls")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    # Story 1.9 — third-party access list (`GET /api/v1/profile/access-list/`).
    path("api/v1/profile/", include("apps.profiles.urls")),
    # Story 1.11 — GDPR Article 20 exports (POST/GET /api/v1/me/gdpr-exports[/{id}[/download]]).
    path("api/v1/me/", include("apps.accounts.gdpr_urls")),
    # Story 2.1 — onboarding step 1 (passions / valeurs / intérêts).
    path("api/v1/students/", include("apps.students.urls")),
    # Story 2.3 — bulletin upload + OCR.
    path("api/v1/students/", include("apps.bulletins.urls")),
    # Story 3.2 — professions referential (admin + student endpoints).
    path("api/v1/", include("apps.professions.urls")),
    # Story 3.4 — scored profession list for student.
    path("api/v1/", include("apps.recommendations.urls")),
    # Story 4.1 — schools & formations referential (admin + public endpoints).
    path("api/v1/", include("apps.schools.urls")),
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
