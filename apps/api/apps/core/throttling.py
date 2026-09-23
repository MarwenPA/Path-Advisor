"""Shared throttle classes — adversarial-review remediation (public SEO endpoints).

A global `DEFAULT_THROTTLE_CLASSES` with an anon rate would silently throttle
every future `AllowAny` endpoint (and the SSR frontend, which fans out several
API calls per page render) — so instead each public SEO view opts in explicitly
via `throttle_classes = [PublicSeoAnonThrottle]`.
"""

from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle


class PublicSeoAnonThrottle(AnonRateThrottle):
    """Per-IP throttle on the anonymous SEO endpoints (Stories 7.1-7.4).

    These endpoints are `AllowAny` and DB-backed, so unauthenticated traffic
    must be bounded. The rate (`public_seo` in `DEFAULT_THROTTLE_RATES`) is
    generous — a single SSR page render triggers a handful of API calls, and
    crawlers burst — but caps a single IP well below anything that could
    hammer the database. Authenticated requests are never throttled here
    (`AnonRateThrottle` only keys on anonymous clients).
    """

    scope = "public_seo"


class RumIngestAnonThrottle(AnonRateThrottle):
    """Per-IP throttle on the anonymous RUM beacon endpoint (Story 8.9).

    One page view flushes ONE batched beacon (up to 5 metrics inside), so a
    real user emits a handful of requests per minute at most. The rate
    (`rum_ingest`) is set well above that but bounds the obvious abuse: the
    endpoint is unauthenticated **and writes to the database**, the exact
    combination the adversarial review flagged on the old anonymous audit
    write. NOTE: the ingest view also sets `authentication_classes = []`, so
    every request is keyed here as anonymous BY DESIGN — a logged-in
    student's beacon must not be attributable (see `telemetry.models`).
    """

    scope = "rum_ingest"
