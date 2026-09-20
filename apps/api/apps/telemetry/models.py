"""Story 8.9 — anonymous Real User Monitoring of Core Web Vitals.

Why this exists: every performance budget in `apps/web/lighthouserc.json`
is calibrated against a *simulated* metric (Lighthouse `throttlingMethod:
simulate`). That gap allowed two bad threshold calls during Epic 7 — a
budget raised on a wrong "runner variance" hypothesis, and a real client-
side render defect hidden behind optimistic aggregation. This table is the
field instrument those decisions lacked.

Privacy is BY CONSTRUCTION, not by policy (the app serves minors — GDPR):

- there is deliberately **no** user FK, no session id, no IP column, no
  user-agent, no full URL. What the schema cannot store cannot leak, and a
  future "let's just log the IP too" change has to touch this model and
  its docstring, where a reviewer will see it;
- `page_type` is a closed enum of PUBLIC page *types*, never a pathname —
  a slug in a URL could identify a niche interest, a page type cannot;
- ingestion (`RumIngestView`) runs with `authentication_classes = []`, so
  even a logged-in student's beacon is processed anonymously.

Rows are aggregates-in-waiting: read access is path_admin-only, and
`prune_rum_vitals` enforces retention (data minimisation).
"""

from __future__ import annotations

from django.db import models


class RumMetric(models.TextChoices):
    LCP = "LCP", "Largest Contentful Paint"
    CLS = "CLS", "Cumulative Layout Shift"
    INP = "INP", "Interaction to Next Paint"
    TTFB = "TTFB", "Time To First Byte"
    FCP = "FCP", "First Contentful Paint"


class RumPageType(models.TextChoices):
    """Closed set of PUBLIC page types (Epic 7 surface). Never a raw path."""

    HOME = "home", "Accueil public"
    METIER_FICHE = "metier_fiche", "Fiche métier publique"
    FORMATION_FICHE = "formation_fiche", "Fiche formation publique"
    DEVENIR_LANDING = "devenir_landing", "Landing devenir-{métier}"
    NIVEAU_LANDING = "niveau_landing", "Landing quel-bac-pour-{métier}"


class RumDevice(models.TextChoices):
    MOBILE = "mobile", "Mobile"
    DESKTOP = "desktop", "Desktop"


class RumConnection(models.TextChoices):
    """`navigator.connection.effectiveType` — absent on Safari/Firefox."""

    SLOW_2G = "slow-2g", "slow-2g"
    TWO_G = "2g", "2g"
    THREE_G = "3g", "3g"
    FOUR_G = "4g", "4g"
    UNKNOWN = "unknown", "unknown"


class RumRating(models.TextChoices):
    """web-vitals' own thresholds bucketing, kept as reported."""

    GOOD = "good", "good"
    NEEDS_IMPROVEMENT = "needs-improvement", "needs-improvement"
    POOR = "poor", "poor"


class RumVital(models.Model):
    metric = models.CharField(max_length=8, choices=RumMetric.choices)
    # ms for timing metrics; unitless score for CLS. Bounds enforced at the
    # serializer (junk floods are cheap to send, cheap to reject).
    value = models.FloatField()
    rating = models.CharField(max_length=20, choices=RumRating.choices)
    page_type = models.CharField(max_length=20, choices=RumPageType.choices)
    device = models.CharField(max_length=10, choices=RumDevice.choices)
    connection = models.CharField(
        max_length=10, choices=RumConnection.choices, default=RumConnection.UNKNOWN
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rum_vitals"
        indexes = [
            # The p75 summary groups by (metric, page_type) over a date range.
            models.Index(fields=["metric", "page_type", "created_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover — admin/debug nicety
        return f"{self.metric} {self.value:.0f} [{self.page_type}/{self.device}]"
