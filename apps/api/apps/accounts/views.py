"""Account endpoints — thin wrappers around dj-rest-auth's registration view.

Adds:
- Per-IP rate limiting (Story 1.3 §AC6 — 5/hour).
- Generic-message response on duplicate emails (CWE-203 user enumeration prevention).
- A `csrf` endpoint the front calls on mount to seed its CSRF cookie before any POST.

Structured signup logging is wired in `apps.accounts.signals` on allauth's `user_signed_up`
signal, so the view itself does not need to know about the freshly-created user.

Duplicate-email detection runs at the serializer level (`SignupSerializer.validate`); the
narrow `IntegrityError` catch below is a backstop for the TOCTOU race between the
`exists()` check and the eventual DB insert.
"""

from __future__ import annotations

from typing import Any

from dj_rest_auth.registration.views import RegisterView, ResendEmailVerificationView
from django.db import IntegrityError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import EmailAlreadyRegistered, RateLimited


class _CsrfResponseSerializer(serializers.Serializer):
    """Drf-spectacular schema for /auth/csrf/."""

    csrf_token = serializers.CharField()


@extend_schema(
    summary="Bootstrap CSRF cookie",
    description=(
        "Seeds the `csrftoken` cookie so the SPA can include `X-CSRFToken` on subsequent "
        "POST/PUT/DELETE requests. Call once on mount."
    ),
    responses={200: _CsrfResponseSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request: Request) -> Response:
    return Response({"csrf_token": get_token(request._request)})


@method_decorator(ratelimit(key="ip", rate="5/h", block=False), name="dispatch")
class ThrottledRegisterView(RegisterView):
    """Signup endpoint — wraps dj-rest-auth's RegisterView with rate limiting + IntegrityError narrowing."""

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if getattr(request, "limited", False):
            raise RateLimited(retry_after_seconds=3600)
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as exc:
            # TOCTOU race: two concurrent signups both pass `SignupSerializer.validate`'s
            # `.exists()` check, then collide at the DB unique constraint. Translate the
            # raw IntegrityError into the same generic Problem we already return at the
            # serializer level, so the public response is uniform regardless of which
            # branch caught the duplicate.
            raise EmailAlreadyRegistered() from exc


@method_decorator(ratelimit(key="ip", rate="5/h", block=False), name="dispatch")
class ThrottledResendEmailView(ResendEmailVerificationView):
    """Resend-email endpoint — wraps dj-rest-auth's view with the same IP throttle.

    Without this wrapper, an attacker could bypass the signup rate limit by repeatedly
    requesting verification-email resends, flooding our SMTP relay and the user's inbox
    (cf. code review §11 patch — abuse vector identified by Edge Case Hunter).
    """

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if getattr(request, "limited", False):
            raise RateLimited(retry_after_seconds=3600)
        return super().create(request, *args, **kwargs)
