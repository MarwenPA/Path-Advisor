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
from django.conf import settings
from django.db import IntegrityError
from django.db.models import F
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework import status as drf_status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.accounts.gdpr_exceptions import (
    GdprExportDownloadCap,
    GdprExportExpired,
    GdprExportNotReady,
)
from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.serializers import GdprExportRequestSerializer
from apps.accounts.services.gdpr_service import (
    GdprExportService,
    gdpr_s3_client,
)
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
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


class _GdprExportCreateThrottle(UserRateThrottle):
    """Defense-in-depth throttle on top of the application 24h rate limit.

    The 24h rate limit (cf. service) handles the legitimate use case. This
    throttle protects against a flood of 429s being used to enumerate user IDs
    if an attacker has stolen credentials but is already rate-limited.
    """

    scope = "gdpr_export_create"
    rate = "50/h"


class _GdprExportCursorPagination(CursorPagination):
    """Cursor pagination keyed on `requested_at` — the canonical timestamp for
    a GDPR export request (the global default `created` does not exist on the
    model).
    """

    ordering = "-requested_at"
    page_size = 50


class GdprExportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """REST surface for GDPR Article 20 exports (Story 1.11).

    - `POST /api/v1/me/gdpr-exports` — creates a pending export.
    - `GET  /api/v1/me/gdpr-exports` — paginated list of the caller's exports.
    - `GET  /api/v1/me/gdpr-exports/{id}` — single export status.
    - `GET  /api/v1/me/gdpr-exports/{id}/download` — 302 to a presigned S3 URL.

    All endpoints scope to `request.user.id`; cross-user IDs surface as 404
    (not 403) so we never leak the existence of someone else's export.
    """

    serializer_class = GdprExportRequestSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = _GdprExportCursorPagination
    lookup_field = "id"

    def get_throttles(self):
        if self.action == "create":
            return [_GdprExportCreateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return GdprExportRequest.objects.none()
        return GdprExportRequest.objects.filter(user_id=self.request.user.id)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        export = GdprExportService.request_export(user=request.user)
        serializer = self.get_serializer(export)
        return Response(serializer.data, status=drf_status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Request, id: str | None = None) -> Response:
        export = self.get_object()

        if export.status == GdprExportStatus.EXPIRED:
            raise GdprExportExpired()
        if export.status != GdprExportStatus.READY:
            raise GdprExportNotReady(
                detail=f"Cet export n'est pas encore prêt (statut : {export.status})."
            )
        if export.download_count >= settings.GDPR_EXPORT_MAX_DOWNLOADS:
            raise GdprExportDownloadCap()
        if not export.archive_s3_key:
            # Defensive: status=ready without an S3 key is an invariant violation.
            raise GdprExportNotReady(detail="Archive introuvable.")

        # Increment the counter and audit BEFORE the redirect — the 302 itself
        # is what S3 will log; whether the user follows it is not knowable
        # client-side. We treat the click as the relevant business event.
        new_count = export.download_count + 1
        GdprExportRequest.objects.filter(pk=export.id).update(
            download_count=F("download_count") + 1,
            last_downloaded_at=timezone.now(),
        )
        record_audit(
            action="gdpr.export_downloaded",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject_id=request.user.id,
            metadata={"export_id": export.id, "download_count": new_count},
        )

        s3 = gdpr_s3_client()
        presigned = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.GDPR_EXPORTS_BUCKET,
                "Key": export.archive_s3_key,
            },
            ExpiresIn=settings.GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS,
        )
        return HttpResponseRedirect(presigned)
