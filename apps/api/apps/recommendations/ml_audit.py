"""Story 9.6 — ML audit metrics over the art. 22 journal (9.5).

The observed metric is each decision's TOP-1 score (the headline
recommendation the student actually sees). No scipy on purpose: the
two-sample KS test is a dozen honest lines (max ECDF gap + the classic
critical value at alpha=0.05), with a >=50-samples floor so noise never pages
anyone.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta
from typing import Any

import structlog
from django.utils import timezone

from .models import ModelVersion, ScoringDecision

log = structlog.get_logger(__name__)

MIN_SAMPLES = 50
BASELINE_SIZE = 500
SUBPOP_MIN_GROUP = 30
BIAS_GAP_THRESHOLD = 0.10
DRIFT_WINDOW_DAYS = 30
DISTRIBUTION_MONTHS = 6


def _top1(decision_scores: list) -> float | None:
    if not decision_scores:
        return None
    try:
        return float(decision_scores[0].get("score", 0))
    except (AttributeError, TypeError, ValueError):
        return None


def ks_statistic(sample_a: list[float], sample_b: list[float]) -> dict[str, Any]:
    """Two-sample Kolmogorov-Smirnov: D = max |ECDF_a - ECDF_b|, compared to
    the alpha=0.05 critical value 1.36·sqrt((n+m)/(n·m)). Below the sample
    floor, the verdict is "insufficient", never an alert."""
    n, m = len(sample_a), len(sample_b)
    if n < MIN_SAMPLES or m < MIN_SAMPLES:
        return {"statistic": None, "threshold": None, "alert": False, "reason": "insufficient"}
    a = sorted(sample_a)
    b = sorted(sample_b)
    d = 0.0
    i = j = 0
    # Ties are consumed on BOTH sides before measuring the ECDF gap — the
    # naive one-side advance inflates D to ~0.5 on identical bimodal
    # samples (caught by the 9.6 live proof, pinned by the ties test).
    while i < n and j < m:
        x = min(a[i], b[j])
        while i < n and a[i] == x:
            i += 1
        while j < m and b[j] == x:
            j += 1
        d = max(d, abs(i / n - j / m))
    threshold = 1.36 * math.sqrt((n + m) / (n * m))
    return {
        "statistic": round(d, 4),
        "threshold": round(threshold, 4),
        "alert": d > threshold,
        "n_baseline": n,
        "n_current": m,
    }


def monthly_score_distribution(months: int = DISTRIBUTION_MONTHS) -> list[dict[str, Any]]:
    since = timezone.now() - timedelta(days=31 * months)
    buckets: dict[str, list[float]] = defaultdict(list)
    rows = ScoringDecision.objects.filter(created_at__gte=since).values_list(
        "created_at", "top_scores"
    )
    for created_at, top_scores in rows.iterator():
        score = _top1(top_scores)
        if score is not None:
            buckets[created_at.strftime("%Y-%m")].append(score)
    return [
        {
            "month": month,
            "count": len(scores),
            "mean": round(sum(scores) / len(scores), 4),
            "min": round(min(scores), 4),
            "max": round(max(scores), 4),
        }
        for month, scores in sorted(buckets.items())
    ]


def capture_baseline(version: ModelVersion) -> bool:
    """Lazily freeze the active version's drift baseline: its first
    BASELINE_SIZE top-1 scores after activation. Returns True when captured."""
    if version.baseline_scores:
        return False
    activated_at = version.deployed_at or version.created_at
    scores = [
        s
        for s in (
            _top1(top)
            for top in ScoringDecision.objects.filter(
                model_version=version, created_at__gte=activated_at
            )
            .order_by("created_at")
            .values_list("top_scores", flat=True)[:BASELINE_SIZE]
        )
        if s is not None
    ]
    if len(scores) < MIN_SAMPLES:
        return False
    version.baseline_scores = scores
    version.save(update_fields=["baseline_scores"])
    log.info("ml_audit.baseline_captured", version=version.version, samples=len(scores))
    return True


def compute_drift(version: ModelVersion, window_days: int = DRIFT_WINDOW_DAYS) -> dict[str, Any]:
    current = [
        s
        for s in (
            _top1(top)
            for top in ScoringDecision.objects.filter(
                model_version=version,
                created_at__gte=timezone.now() - timedelta(days=window_days),
            ).values_list("top_scores", flat=True)
        )
        if s is not None
    ]
    return ks_statistic([float(x) for x in version.baseline_scores], current)


def subpopulation_gaps(window_days: int = DRIFT_WINDOW_DAYS) -> dict[str, Any]:
    """Mean top-1 by niveau and by filière over the window (groups with
    ≥ SUBPOP_MIN_GROUP decisions). Relative gap > 10% arms the bias alert."""
    since = timezone.now() - timedelta(days=window_days)
    rows = ScoringDecision.objects.filter(created_at__gte=since).values_list(
        "top_scores",
        "user__student_profile__level_profile__level",
        "user__student_profile__level_profile__filiere",
    )
    by_dim: dict[str, dict[str, list[float]]] = {
        "niveau": defaultdict(list),
        "filiere": defaultdict(list),
    }
    for top_scores, level, filiere in rows.iterator():
        score = _top1(top_scores)
        if score is None:
            continue
        if level:
            by_dim["niveau"][level].append(score)
        if filiere:
            by_dim["filiere"][filiere].append(score)

    result: dict[str, Any] = {"dimensions": {}, "max_gap": 0.0, "alert": False}
    for dim, groups in by_dim.items():
        means = {
            group: round(sum(scores) / len(scores), 4)
            for group, scores in groups.items()
            if len(scores) >= SUBPOP_MIN_GROUP
        }
        gap = 0.0
        if len(means) >= 2 and max(means.values()) > 0:
            values = list(means.values())
            gap = (max(values) - min(values)) / max(values)
        result["dimensions"][dim] = {
            "groups": means,
            "gap": round(gap, 4),
            "counts": {g: len(s) for g, s in groups.items()},
        }
        result["max_gap"] = max(result["max_gap"], gap)
    result["alert"] = result["max_gap"] > BIAS_GAP_THRESHOLD
    result["max_gap"] = round(result["max_gap"], 4)
    return result


def build_audit_report() -> dict[str, Any]:
    """The /admin/ml-audit payload — computed on demand from the journal."""
    active = ModelVersion.objects.filter(is_active=True).first()
    drift: dict[str, Any] = {
        "statistic": None,
        "threshold": None,
        "alert": False,
        "reason": "no-active-model",
    }
    if active is not None:
        capture_baseline(active)
        drift = compute_drift(active)
    return {
        "model": (
            {
                "version": active.version,
                "deployed_at": active.deployed_at.isoformat() if active.deployed_at else None,
                "baseline_size": len(active.baseline_scores),
                "requires_ethics_review": active.requires_ethics_review,
            }
            if active
            else None
        ),
        "monthly": monthly_score_distribution(),
        "drift": drift,
        "subpopulations": subpopulation_gaps(),
    }
