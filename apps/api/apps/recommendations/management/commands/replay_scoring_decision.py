"""Story 9.5 — art. 22 replay: recompute an archived decision against the
archived model version and diff the outputs."""

from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.recommendations.model_governance import replay_decision
from apps.recommendations.models import ScoringDecision


class Command(BaseCommand):
    help = "Rejoue une décision de scoring archivée et diffe les sorties."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("decision_id")

    def handle(self, *args: Any, **options: Any) -> None:
        decision = (
            ScoringDecision.objects.select_related("model_version")
            .filter(pk=options["decision_id"])
            .first()
        )
        if decision is None:
            raise CommandError("Décision inconnue.")
        report = replay_decision(decision)
        self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False))
        if report["match"]:
            self.stdout.write(self.style.SUCCESS("Rejeu conforme — décision reproductible."))
        else:
            raise CommandError(
                f"{len(report['diffs'])} écart(s) au rejeu — investiguer (registre/poids)."
            )
