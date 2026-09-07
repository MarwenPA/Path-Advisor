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
