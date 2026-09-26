"""Story 9.5/9.6 — beat tasks: art. 22 journal retention (+ ML audit, 9.6)."""

from __future__ import annotations

import structlog
from celery import shared_task

log = structlog.get_logger(__name__)


@shared_task(name="recommendations.prune_scoring_decisions")
def prune_scoring_decisions_task(days: int = 365) -> int:
    """Story 9.5 — art. 22 journal retention (12 months, DPO note in the
    story doc). Personal data of minors must not accumulate forever."""
    from .model_governance import prune_scoring_decisions

    deleted = prune_scoring_decisions(days=days)
    log.info("recommendations.pruned_scoring_decisions", deleted=deleted, days=days)
    return deleted


@shared_task(name="recommendations.run_ml_audit")
def run_ml_audit() -> dict:
    """Story 9.6 — weekly drift + bias audit on the active model.

    Cross-user read → `with_system_actor` (whitelisted in core/rls.py).
    Any alert writes an `ml.audit_alert` audit row and emails the active
    path_admins with the review workflow (retrain? rollback via 9.5?).
    A bias alert additionally flags the active version for ethics review.
    Slack: not wired (no webhook in the infra) — consigned in the story doc.
    """
    from apps.accounts.models import User, UserRole, UserStatus
    from apps.audit.decorators import record_audit
    from apps.core.rls import with_system_actor
    from apps.mailer.service import send_transactional

    from .ml_audit import build_audit_report
    from .models import ModelVersion

    with with_system_actor(reason="recommendations.ml_audit_beat"):
        report = build_audit_report()
        drift_alert = bool(report["drift"].get("alert"))
        bias_alert = bool(report["subpopulations"].get("alert"))

        if bias_alert:
            ModelVersion.objects.filter(is_active=True).update(requires_ethics_review=True)

        if drift_alert or bias_alert:
            record_audit(
                action="ml.audit_alert",
                result="alert",
                metadata={
                    "drift": report["drift"],
                    "max_subpopulation_gap": report["subpopulations"]["max_gap"],
                    "model": (report["model"] or {}).get("version"),
                },
            )
            admins = User.objects.filter(
                role=UserRole.PATH_ADMIN, status=UserStatus.ACTIVE
            ).values_list("email", flat=True)
            for email in admins:
                send_transactional(
                    template_app="recommendations",
                    template_base="email/ml_audit_alert",
                    to=email,
                    context={
                        "model_version": (report["model"] or {}).get("version", "inconnu"),
                        "drift_alert": drift_alert,
                        "drift_statistic": report["drift"].get("statistic"),
                        "drift_threshold": report["drift"].get("threshold"),
                        "bias_alert": bias_alert,
                        "max_gap_percent": round(report["subpopulations"]["max_gap"] * 100),
                    },
                )
            log.error(
                "ml_audit.alert",
                drift=drift_alert,
                bias=bias_alert,
                admins_notified=len(list(admins)),
            )
        else:
            log.info(
                "ml_audit.ok", drift=report["drift"], max_gap=report["subpopulations"]["max_gap"]
            )

    return {
        "drift_alert": drift_alert,
        "bias_alert": bias_alert,
    }
