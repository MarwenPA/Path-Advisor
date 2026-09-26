"""Story 9.5 — model-version governance: registration, ethics-gated
activation, decision replay, journal retention.

Every write is audited; activation is EXCLUSIVE (one active version) and
refused while the evaluation metrics show a >10% inter-group gap without a
recorded ethics review (the AC's "alerte avant déploiement").
"""

from __future__ import annotations

import hashlib
import json

import structlog
from django.db import transaction
from django.utils import timezone

from apps.audit.decorators import record_audit

from .models import ModelVersion, ScoringDecision

log = structlog.get_logger(__name__)

ETHICS_GAP_THRESHOLD = 0.10
DECISION_RETENTION_DAYS = 365


class EthicsGateError(Exception):
    """Activation refused: inter-group gap above threshold, no review note."""


def compute_dataset_hash() -> str:
    """SHA256 of the calibration dataset: the ACTIVE professions' signal
    space, sorted for determinism."""
    from apps.professions.models import Profession

    corpus = [
        {
            "slug": p.slug,
            "signals": p.signals_json or {},
            "levels": sorted(p.level_compatibility or []),
        }
        for p in Profession.objects.filter(is_active=True).order_by("slug")
    ]
    return hashlib.sha256(
        json.dumps(corpus, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def register_model_version(
    *,
    editor,
    name: str,
    version: str,
    hyperparameters: dict,
    evaluation_metrics: dict | None = None,
) -> ModelVersion:
    row = ModelVersion.objects.create(
        name=name,
        version=version,
        dataset_hash=compute_dataset_hash(),
        hyperparameters_json=hyperparameters,
        evaluation_metrics_json=evaluation_metrics or {},
    )
    gap = row.max_subpopulation_gap()
    if gap > ETHICS_GAP_THRESHOLD:
        row.requires_ethics_review = True
        row.save(update_fields=["requires_ethics_review"])
    record_audit(
        action="ml.model_version_registered",
        result="success",
        actor=editor,
        subject_id=row.pk,
        metadata={"version": version, "max_subpopulation_gap": round(gap, 4)},
    )
    return row


def activate_model_version(
    *, version_row: ModelVersion, editor, ethics_note: str = ""
) -> ModelVersion:
    """Ethics-gated, exclusive activation (the AC's pre-deployment alert)."""
    gap = version_row.max_subpopulation_gap()
    if gap > ETHICS_GAP_THRESHOLD and not (
        ethics_note.strip() or version_row.ethics_review_note.strip()
    ):
        raise EthicsGateError(
            f"Écart inter-groupes de {gap:.0%} (> {ETHICS_GAP_THRESHOLD:.0%}) — "
            "une note de revue éthique est obligatoire avant l'activation."
        )
    with transaction.atomic():
        ModelVersion.objects.filter(is_active=True).exclude(pk=version_row.pk).update(
            is_active=False
        )
        version_row.is_active = True
        version_row.deployed_at = timezone.now()
        version_row.deployed_by = editor
        if ethics_note.strip():
            version_row.ethics_review_note = ethics_note.strip()
            version_row.requires_ethics_review = False
        version_row.save(
            update_fields=[
                "is_active",
                "deployed_at",
                "deployed_by",
                "ethics_review_note",
                "requires_ethics_review",
            ]
        )
        record_audit(
            action="ml.model_version_activated",
            result="success",
            actor=editor,
            subject_id=version_row.pk,
            metadata={
                "version": version_row.version,
                "max_subpopulation_gap": round(gap, 4),
                "ethics_note_recorded": bool(version_row.ethics_review_note),
            },
        )
    return version_row


def replay_decision(decision: ScoringDecision) -> dict:
    """Art. 22 replay: re-send the archived inputs to the ai-service pinned
    on the archived version, and diff the top scores. Returns
    {"match": bool, "diffs": [...], "replayed_version": str}."""
    from .services.ai_client import ai_client

    snapshot = decision.inputs_snapshot
    response = ai_client.score_metiers(
        student_id=f"replay-{decision.pk}",
        profile=snapshot["profile"],
        occupation_ids=snapshot["occupation_ids"],
        professions_data=snapshot.get("professions_data"),
        model_version=decision.model_version.version,
    )
    replayed = {
        item["occupation_id"]: round(float(item.get("score", 0)), 4)
        for item in response.get("scored_occupations", [])
    }
    diffs = []
    for entry in decision.top_scores:
        recorded = round(float(entry["score"]), 4)
        fresh = replayed.get(entry.get("id"))
        if fresh is None or abs(fresh - recorded) > 0.01:
            diffs.append({"slug": entry["slug"], "recorded": recorded, "replayed": fresh})
    return {
        "match": not diffs,
        "diffs": diffs,
        "replayed_version": response.get("model_version", ""),
    }


def prune_scoring_decisions(days: int = DECISION_RETENTION_DAYS) -> int:
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=max(30, days))
    deleted, _ = ScoringDecision.objects.filter(created_at__lt=cutoff).delete()
    return deleted
