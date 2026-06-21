"""AdmissionPredictionService — Story 4.2.

Fourchette d'admission personnalisée :
  - min  = max(5, expected - spread)
  - max  = min(95, expected + spread)
  - spread = 15 if has_bulletins else 25  (fourchette élargie sans bulletins)

Étiquette qualitative (avant override has_bulletins) :
  - >= 70 → sur
  - >= 45 → realiste
  - < 45  → audacieux

Si has_bulletins=False → label forcé à estimation_indicative.

Garde-fou anti-humiliation : expected_proba jamais < 5%.

Context line and action lever generated from label and profile data.
UX-DR25 compliant — no visual difference between complete/incomplete profile
beyond context_line suffix.

This service is pure computation: no external API calls in MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.schools.models import AdmissionStat, School


@dataclass
class AdmissionPrediction:
    """Result of a single admission probability prediction."""

    min_proba: int
    expected_proba: int
    max_proba: int
    label: str
    context_line: str
    action_lever: str


class AdmissionPredictionService:
    """Compute a personalised admission probability range for a school.

    All logic is deterministic (no external I/O). Call `predict()` for a
    one-shot result, or `upsert_stat()` to persist it.
    """

    # Base expected probability indexed by selectivity_index (1=très sélectif, 5=non sélectif)
    _BASE_PROBA: dict[int, int] = {1: 20, 2: 35, 3: 55, 4: 75, 5: 90}

    def predict(
        self,
        school: School,
        average_grade: float | None = None,
        has_bulletins: bool = False,
        selectivity_override: int | None = None,
    ) -> AdmissionPrediction:
        """Compute an admission range for (school, student_profile).

        Args:
            school: The target school instance. `selectivity_index` is read
                from it unless `selectivity_override` is given.
            average_grade: Student average grade (e.g. 12.5/20).  If None,
                only the school selectivity drives the base probability.
            has_bulletins: Whether the student has uploaded their grade reports.
                False → wider uncertainty range + estimation_indicative label.
            selectivity_override: Override the school's selectivity_index for
                testing or hypothetical scenarios.

        Returns:
            An AdmissionPrediction dataclass with all prediction fields.
        """
        selectivity = (
            selectivity_override if selectivity_override is not None else school.selectivity_index
        )

        # Base expected probability from selectivity
        expected = self._BASE_PROBA.get(selectivity, 55)

        # Adjust by grade if provided (pivot at 12/20, ±3 pp per grade point)
        if average_grade is not None:
            grade_bonus = int((average_grade - 12.0) * 3)
            expected = max(5, min(95, expected + grade_bonus))

        # Anti-humiliation floor: never below 5%
        expected = max(5, expected)

        # Spread: narrower with bulletins (more data → more confidence)
        spread = 15 if has_bulletins else 25

        min_p = max(5, expected - spread)
        max_p = min(95, expected + spread)

        # Qualitative label based on expected probability
        if expected >= 70:
            label = AdmissionStat.Label.SUR
            context_line = "Ton profil correspond bien à ce type d'établissement."
            action_lever = ""
        elif expected >= 45:
            label = AdmissionStat.Label.REALISTE
            context_line = "Tu as de bonnes chances d'être admis·e."
            action_lever = "Continue à maintenir tes résultats actuels."
        else:
            label = AdmissionStat.Label.AUDACIEUX
            context_line = "Ce pari est ambitieux — c'est faisable avec du travail ciblé."
            action_lever = "Renforce tes matières les plus décisives pour ce parcours."

        # Without bulletins: override label and context (less personalised)
        if not has_bulletins:
            label = AdmissionStat.Label.ESTIMATION_INDICATIVE
            context_line = "Estimation basée sur les statistiques de l'établissement."
            action_lever = "Ajoute tes bulletins pour une prédiction personnalisée."

        return AdmissionPrediction(
            min_proba=min_p,
            expected_proba=expected,
            max_proba=max_p,
            label=label,
            context_line=context_line,
            action_lever=action_lever,
        )

    def upsert_stat(
        self,
        school: School,
        user=None,
        average_grade: float | None = None,
        has_bulletins: bool = False,
    ) -> AdmissionStat:
        """Persist (or refresh) an AdmissionStat row for (school, user).

        Idempotent: calling twice keeps a single DB row and captures the
        previous expected_proba for delta display.

        Args:
            school: The target school instance.
            user: The authenticated user, or None for the population baseline.
            average_grade: Student average grade passed to predict().
            has_bulletins: Passed to predict().

        Returns:
            The created or updated AdmissionStat instance.
        """
        prediction = self.predict(school, average_grade, has_bulletins)

        # Capture previous value before overwriting (for delta / trend UI)
        existing = AdmissionStat.objects.filter(school=school, user=user).first()
        previous_proba = existing.expected_proba if existing else None

        stat, _ = AdmissionStat.objects.update_or_create(
            school=school,
            user=user,
            defaults={
                "min_proba": prediction.min_proba,
                "expected_proba": prediction.expected_proba,
                "max_proba": prediction.max_proba,
                "label": prediction.label,
                "context_line": prediction.context_line,
                "action_lever": prediction.action_lever,
                "previous_proba": previous_proba,
            },
        )
        return stat
