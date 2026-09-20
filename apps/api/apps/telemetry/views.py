"""Story 8.9 — RUM ingest (anonymous, write-only) + p75 summary (path_admin).

Two deliberately asymmetric endpoints:

- `POST /api/v1/rum/vitals/` — the beacon sink. `AllowAny`, throttled, and
  `authentication_classes = []` so a logged-in student's beacon can never be
  associated with their session (privacy by construction — see
  `telemetry.models`). Empty auth also means DRF's `SessionAuthentication`
  CSRF check never runs: the frontend sends the beacon with
  `credentials: "omit"`, so there is no cookie to protect. The write is the
  only thing this endpoint can do, and it is bounded (batch ≤ 10, enums,
  value caps, per-IP throttle).

- `GET /api/v1/admin/rum/summary/` — the reading side, path_admin only.
  Returns p75 per (metric, page_type) with device/connection segment
  breakdowns (AC2/AC3). p75 is Google's ranking threshold, so that is the
  number budgets get calibrated against.

p75 is computed in Python rather than `percentile_cont` SQL: the SQLite
fast-test lane has no percentile aggregate, and a same-code path on both
engines beats a vendor branch. Volume is bounded by the date window and
retention (`prune_rum_vitals`); revisit if row counts ever make this slow.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAuthenticatedAndActive, IsPathAdmin
from apps.core.throttling import RumIngestAnonThrottle

from .models import RumVital
from .serializers import RumIngestSerializer

#: Default and ceiling for the summary window. 28 days matches the CrUX
#: collection window Google uses for the same metrics.
DEFAULT_WINDOW_DAYS = 28
MAX_WINDOW_DAYS = 90


def _p75(values: list[float]) -> float:
    """Nearest-rank 75th percentile; callers guarantee a non-empty list."""
    ordered = sorted(values)
    # Nearest-rank: smallest value with at least 75% of the sample at or
    # below it. Matches how CrUX buckets read (a "p75 = X" means 75% of
    # experiences were at least this good).
    rank = max(0, -(-75 * len(ordered) // 100) - 1)
    return ordered[rank]


class RumIngestView(APIView):
    # Plain assignments, not ClassVar — mypy refuses ClassVar overrides of
    # APIView's instance-typed attributes (same convention as story 1.16's
    # throttle wiring).
    permission_classes = [AllowAny]
    authentication_classes = []  # anonymity by construction — see module docstring
    throttle_classes = [RumIngestAnonThrottle]

    def post(self, request: Request) -> Response:
        serializer = RumIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # 204: the beacon fires on pagehide — nobody reads the body.
        return Response(status=status.HTTP_204_NO_CONTENT)


class RumSummaryView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request) -> Response:
        try:
            days = int(request.query_params.get("days", DEFAULT_WINDOW_DAYS))
        except ValueError:
            days = DEFAULT_WINDOW_DAYS
        days = max(1, min(days, MAX_WINDOW_DAYS))
        since = timezone.now() - timedelta(days=days)

        rows = RumVital.objects.filter(created_at__gte=since).values_list(
            "metric", "page_type", "device", "connection", "value"
        )

        # (metric, page_type) → values + per-segment values. Segments answer
        # AC2's "who is actually slow" question — a global median would hide
        # exactly the population this exists to protect (mobile on slow
        # networks).
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        for metric, page_type, device, connection, value in rows:
            g = groups.setdefault(
                (metric, page_type),
                {"values": [], "by_device": {}, "by_connection": {}},
            )
            g["values"].append(value)
            g["by_device"].setdefault(device, []).append(value)
            g["by_connection"].setdefault(connection, []).append(value)

        summary = [
            {
                "metric": metric,
                "page_type": page_type,
                "count": len(g["values"]),
                "p75": _p75(g["values"]),
                "by_device": {
                    d: {"count": len(vs), "p75": _p75(vs)} for d, vs in g["by_device"].items()
                },
                "by_connection": {
                    c: {"count": len(vs), "p75": _p75(vs)} for c, vs in g["by_connection"].items()
                },
            }
            for (metric, page_type), g in sorted(groups.items())
        ]
        return Response({"window_days": days, "summary": summary})
