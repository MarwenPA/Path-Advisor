"""DPO endpoints — paginated read + CSV export.

Both endpoints:
- Require `IsPathAdmin` (else 403 + `audit.log_query_denied` recorded).
- Are themselves audited: a `audit.log_queried` (or `audit.log_exported`) row
  is written on every call. This is the meta-audit required by FR12.
- Wire the `core.request_context` so the audit entries carry the calling
  user's id/role/ip. Story 1.7 will move this wiring to a global middleware;
  for Story 1.13 each endpoint sets up the context explicitly.
"""

from __future__ import annotations

import csv
import functools
import json
from datetime import UTC, datetime
from typing import Any, ClassVar

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.decorators import record_audit
from apps.audit.models import AuditLog, AuditResult
from apps.audit.permissions import IsPathAdmin
from apps.audit.serializers import AuditLogSerializer
from apps.audit.tasks import export_csv_to_s3
from apps.core import request_context

# ---------- helpers ----------


def _with_audit_context(view_func):
    """Set thread-local audit context for the duration of the view call.

    For non-streaming responses the `finally` clears after the response is
    built. For `StreamingHttpResponse` we attach a `close` callback so the
    clear happens after the generator is exhausted (otherwise the streaming
    body would record audit rows with an empty actor).
    """

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        request_context.set_actor_from_request(request)
        try:
            response = view_func(request, *args, **kwargs)
        except Exception:
            request_context.clear()
            raise
        # `Closable` Django responses fire `close()` once the WSGI/ASGI runner
        # finishes streaming; tie thread-local cleanup to that callback.
        existing_close = getattr(response, "close", None)

        def _close_and_clear():
            if existing_close is not None:
                existing_close()
            request_context.clear()

        response.close = _close_and_clear  # type: ignore[assignment]
        return response

    return wrapper


_ALLOWED_FILTER_KEYS = {"subject_id", "actor_id", "action", "result", "tenant_id"}


class AuditLogCursorPagination(CursorPagination):
    """Cursor on `created_at` — matches the indexed read pattern."""

    ordering = "-created_at"
    page_size = 50


def _apply_filters(qs, params: dict[str, Any]):
    from uuid import UUID

    from apps.core.exceptions import DomainError

    class _InvalidFilter(DomainError):
        type = "https://path-advisor.fr/errors/invalid-filter"
        title = "Filtre invalide"

    filters: dict[str, Any] = {}
    if value := params.get("subject_id"):
        filters["subject_id"] = value
    if value := params.get("actor_id"):
        filters["actor_id"] = value
    if value := params.get("action"):
        # Support `auth.*` prefix matching via trailing `.` convention.
        if value.endswith("."):
            filters["action__startswith"] = value
        else:
            filters["action"] = value
    if value := params.get("result"):
        filters["result"] = value
    if value := params.get("tenant_id"):
        try:
            filters["tenant_id"] = UUID(value)
        except (TypeError, ValueError) as exc:
            raise _InvalidFilter(detail=f"tenant_id is not a valid UUID: {value}") from exc

    qs = qs.filter(**filters)

    if value := params.get("from"):
        dt = parse_datetime(value)
        if dt:
            qs = qs.filter(created_at__gte=dt)
    if value := params.get("to"):
        dt = parse_datetime(value)
        if dt:
            qs = qs.filter(created_at__lte=dt)
    return qs


def _validated_filters(params: dict[str, Any]) -> dict[str, Any]:
    """Subset of the raw query params we audit alongside each call — no PII fields included."""
    return {
        k: v
        for k, v in params.items()
        if k in _ALLOWED_FILTER_KEYS or k in ("from", "to", "action")
    }


def _flatten_params(query_params: Any) -> dict[str, str]:
    """Collapse a `QueryDict` to `{key: value}` for JSON-friendly audit metadata.

    Audit endpoints accept single-valued filters only. If a caller passes
    multi-values (`?action=a&action=b`), we keep the LAST value and add a
    `_multi_value_keys` marker so the audit metadata makes it explicit
    the request was malformed and we silently picked one.
    """
    flat: dict[str, str] = {}
    multi: list[str] = []
    getlist = getattr(query_params, "getlist", None)
    for key in query_params:
        if callable(getlist):
            values = getlist(key)
            if len(values) > 1:
                multi.append(key)
            flat[key] = values[-1]
        else:
            flat[key] = query_params.get(key)
    if multi:
        flat["_multi_value_keys"] = ",".join(sorted(multi))
    return flat


# ---------- views ----------


@extend_schema(
    summary="List audit log entries (DPO)",
    description=(
        "Returns paginated audit entries. Restricted to `path_admin` users. "
        "Each call is itself recorded as `audit.log_queried` (FR12 meta-audit)."
    ),
    parameters=[
        OpenApiParameter(name="subject_id", required=False, type=str),
        OpenApiParameter(name="actor_id", required=False, type=str),
        OpenApiParameter(
            name="action",
            required=False,
            type=str,
            description="Exact match, or prefix match if value ends with `.` (e.g. `outreach.`)",
        ),
        OpenApiParameter(
            name="result", required=False, type=str, enum=["success", "failure", "denied"]
        ),
        OpenApiParameter(name="tenant_id", required=False, type=str),
        OpenApiParameter(name="from", required=False, type=str, description="ISO 8601 lower bound"),
        OpenApiParameter(name="to", required=False, type=str, description="ISO 8601 upper bound"),
    ],
)
class AuditLogListView(ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes: ClassVar[list] = [IsAuthenticated, IsPathAdmin]
    pagination_class = AuditLogCursorPagination
    queryset = AuditLog.objects.all().order_by("-created_at")

    def dispatch(self, request, *args, **kwargs):
        request_context.set_actor_from_request(request)
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            request_context.clear()

    def get_queryset(self):
        return _apply_filters(super().get_queryset(), self.request.query_params)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        # Meta-audit: this very call lands in the journal it returned.
        # `count` is absent from CursorPagination responses, so we surface the
        # page size that was actually returned to the caller — the previous
        # `result_count` name implied a full-dataset total it never was.
        page_returned = (
            len(response.data.get("results", [])) if isinstance(response.data, dict) else 0
        )
        record_audit(
            action="audit.log_queried",
            result=AuditResult.SUCCESS,
            metadata={
                "filters": _validated_filters(_flatten_params(request.query_params)),
                "page_size_returned": page_returned,
            },
        )
        return response


@extend_schema(
    summary="Export audit log entries as CSV (DPO)",
    description=(
        "Streams a CSV with the same filters as `GET /audit/logs/`. Above "
        "`AUDIT_EXPORT_SYNC_THRESHOLD` rows the response is `202 Accepted` "
        "and a Celery task pushes the file to S3."
    ),
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPathAdmin])
@_with_audit_context
def audit_log_export_csv(request: Request) -> HttpResponse:
    params = _flatten_params(request.query_params)
    qs = _apply_filters(AuditLog.objects.all().order_by("created_at"), params)
    count = qs.count()
    threshold = getattr(settings, "AUDIT_EXPORT_SYNC_THRESHOLD", 10_000)

    if count > threshold:
        # Async path — Celery delivers the gz CSV to S3 (signed URL valid 7 days).
        export_csv_to_s3.delay(filters=_validated_filters(params), requested_by=request.user.id)
        record_audit(
            action="audit.log_exported",
            result=AuditResult.SUCCESS,
            metadata={
                "format": "csv",
                "filters": _validated_filters(params),
                "row_count": count,
                "synchronous": False,
            },
        )
        # The Celery task is responsible for generating the presigned URL +
        # uploading to `exports-gdpr`. The 202 response tells the DPO their
        # job is in flight; the task return value carries the download URL
        # which a future email/notification will deliver (Story 1.13 §AC5
        # "lien valable 7 jours", currently surfaced via task result only).
        return Response(
            {
                "detail": "Export queued — download link will be delivered when ready.",
                "row_count": count,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    response = StreamingHttpResponse(
        _stream_csv(qs),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="audit-log-export-{datetime.now(UTC):%Y%m%d}.csv"'
    )
    record_audit(
        action="audit.log_exported",
        result=AuditResult.SUCCESS,
        metadata={
            "format": "csv",
            "filters": _validated_filters(params),
            "row_count": count,
            "synchronous": True,
        },
    )
    return response


_CSV_COLUMNS = (
    "id",
    "created_at",
    "actor_id",
    "actor_role",
    "subject_id",
    "action",
    "result",
    "tenant_id",
    "metadata_json",
)


class _Echo:
    """File-like stub for `csv.writer` so we can stream without buffering."""

    def write(self, value: str) -> str:
        return value


def _stream_csv(qs):
    writer = csv.writer(_Echo())
    # UTF-8 BOM so Excel correctly decodes accented French / Arabic metadata.
    yield "﻿"
    yield writer.writerow(_CSV_COLUMNS)
    for row in qs.iterator(chunk_size=500):
        yield writer.writerow(
            (
                row.id,
                row.created_at.isoformat(),
                row.actor_id or "",
                row.actor_role,
                row.subject_id or "",
                row.action,
                row.result,
                str(row.tenant_id) if row.tenant_id else "",
                json.dumps(row.metadata, sort_keys=True, default=str),
            )
        )
