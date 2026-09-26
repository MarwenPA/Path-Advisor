"""Story 9.5 — model versioning + the art. 22 scoring-decision journal.

Split module (imported by `models.py` so Django's app registry and
makemigrations see it) — keeps the 3.11 review models untouched.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.ids import generate_id


def _default_model_version_id() -> str:
    return generate_id("mv")


def _default_decision_id() -> str:
    return generate_id("scd")


class ModelVersion(models.Model):
    """One deployable version of the recommendation model.

    Today's "model" is the 3.3 statistical scorer: a version = (scorer code,
    dimension WEIGHTS, calibration dataset). The ai-service serves archived
    versions through its MODEL_REGISTRY, which makes every logged decision
    replayable (art. 22). Exactly one row is active at a time.

    Ethics gate (AC): activation is refused (409) while the evaluation
    metrics show a >10% inter-group gap and no `ethics_review_note` exists.
    No RLS: governance data, no student PII.
    """

    id = models.CharField(
        default=_default_model_version_id, editable=False, max_length=32, primary_key=True
    )
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50, unique=True)
    #: SHA256 of the calibration dataset. The pre-9.5 seed carries the
    #: honest marker "unversioned-legacy" — nobody hashed it back then.
    dataset_hash = models.CharField(max_length=80)
    hyperparameters_json = models.JSONField(default=dict)
    #: May carry {"subpopulations": {"<dim>": {"<group>": score, ...}}} —
    #: the ethics gate reads inter-group gaps from here BEFORE deployment.
    evaluation_metrics_json = models.JSONField(default=dict)
    is_active = models.BooleanField(default=False, db_index=True)
    requires_ethics_review = models.BooleanField(default=False)
    ethics_review_note = models.TextField(blank=True, default="")
    deployed_at = models.DateTimeField(null=True, blank=True)
    deployed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    #: Story 9.6 — score sample captured after activation, the KS-drift
    #: baseline. Filled lazily by the audit task (bounded list of floats).
    baseline_scores = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_versions"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.version}{' [active]' if self.is_active else ''}"

    def max_subpopulation_gap(self) -> float:
        """Largest relative inter-group gap across evaluation subpopulations
        (0.0 when none declared). >0.10 arms the ethics gate."""
        worst = 0.0
        for groups in (self.evaluation_metrics_json.get("subpopulations") or {}).values():
            values = [v for v in groups.values() if isinstance(v, (int, float))]
            if len(values) >= 2 and max(values) > 0:
                worst = max(worst, (max(values) - min(values)) / max(values))
        return worst


class ScoringDecision(models.Model):
    """Art. 22 journal — one row per recommendation computation.

    `inputs_snapshot` is the EXACT payload sent to the ai-service (profile
    signals + niveau + bulletin summary): together with the version's
    archived weights it makes the decision replayable
    (`replay_scoring_decision`). `top_scores` is bounded (top 15).

    PROTECT on the version: a model that produced decisions is never
    deleted. RLS from the initial migration (a minor's vocational inputs
    are personal data) — policies mirror `notification_preferences`.
    Retention: 365 days (beat prune; DPO note in the story doc).
    """

    id = models.CharField(
        default=_default_decision_id, editable=False, max_length=32, primary_key=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scoring_decisions"
    )
    model_version = models.ForeignKey(
        ModelVersion, on_delete=models.PROTECT, related_name="decisions"
    )
    inputs_snapshot = models.JSONField()
    top_scores = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "scoring_decisions"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"{self.user_id} @ {self.model_version_id} ({self.created_at:%Y-%m-%d})"
