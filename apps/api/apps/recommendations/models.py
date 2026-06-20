"""Recommendation models.

RecommendationReview (Story 3.7): RGPD art. 22 human review request.
A student can contest one recommendation per profession (unique_together).
"""

from __future__ import annotations

from django.db import models

from apps.core.ids import generate_id


def _default_review_id() -> str:
    return generate_id("rev")


class RecommendationReview(models.Model):
    """Student-initiated human review request for a vocational recommendation.

    RGPD art. 22 right to human intervention in automated scoring decisions.
    One request per (student, profession) — enforced by unique_together.
    """

    class Reason(models.TextChoices):
        NE_CORRESPOND_PAS = "ne_correspond_pas", "Ne me correspond pas du tout"
        CHOQUANT = "choquant_inapproprie", "Métier choquant ou inapproprié"
        AUTRE = "autre", "Autre"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        RESOLVED_CORRECT = "resolved_correct", "Reco correcte — expliqué"
        RESOLVED_FIXED = "resolved_fixed", "Modèle ajusté"

    id = models.CharField(
        default=_default_review_id,
        editable=False,
        max_length=32,
        primary_key=True,
    )
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="recommendation_reviews",
        db_index=True,
    )
    profession = models.ForeignKey(
        "professions.Profession",
        on_delete=models.CASCADE,
        related_name="recommendation_reviews",
        db_index=True,
    )
    reason = models.CharField(max_length=30, choices=Reason.choices)
    comment = models.TextField(max_length=500, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recommendation Review"
        verbose_name_plural = "Recommendation Reviews"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "profession"],
                name="unique_student_profession_review",
            )
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="recomm_status_created_idx"),
        ]

    def __str__(self) -> str:
        return f"ReviewRequest({self.reason}) by {self.student_id} on {self.profession_id}"
