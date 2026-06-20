"""Serializers for the recommendations app — Story 3.7."""

from __future__ import annotations

from rest_framework import serializers

from .models import RecommendationReview


class RecommendationReviewCreateSerializer(serializers.Serializer):
    """Validates incoming POST payload from the student."""

    profession_slug = serializers.SlugField()
    reason = serializers.ChoiceField(choices=RecommendationReview.Reason.choices)
    comment = serializers.CharField(
        max_length=500,
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class RecommendationReviewResponseSerializer(serializers.ModelSerializer):
    """201 Created response — minimal shape."""

    class Meta:
        model = RecommendationReview
        fields = ["id", "status"]


class RecommendationReviewAdminSerializer(serializers.ModelSerializer):
    """Full representation for admin list endpoint."""

    profession_slug = serializers.CharField(source="profession.slug", read_only=True)
    student_id = serializers.CharField(source="student.id", read_only=True)

    class Meta:
        model = RecommendationReview
        fields = [
            "id",
            "profession_slug",
            "student_id",
            "reason",
            "comment",
            "status",
            "created_at",
        ]
