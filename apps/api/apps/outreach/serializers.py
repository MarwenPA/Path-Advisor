"""Serializers for early-outreach requests — Stories 5.4 + 5.5."""

from __future__ import annotations

from rest_framework import serializers

from apps.outreach.models import EarlyOutreachRequest

MOTIVATION_MIN_WORDS = 200
MOTIVATION_MAX_WORDS = 500


def _validate_motivation_word_count(value: str) -> str:
    """Story 5.5 AC — when a motivation is provided at all, it must be
    200-500 words (an empty motivation is still allowed — Story 5.4 kept it
    optional, and the epic doesn't force every student to write one)."""
    stripped = value.strip()
    if not stripped:
        return value
    word_count = len(stripped.split())
    if word_count < MOTIVATION_MIN_WORDS or word_count > MOTIVATION_MAX_WORDS:
        raise serializers.ValidationError(
            f"Ta motivation doit faire entre {MOTIVATION_MIN_WORDS} et "
            f"{MOTIVATION_MAX_WORDS} mots (actuellement {word_count})."
        )
    return value


class EarlyOutreachCreateSerializer(serializers.Serializer):
    """AC2 — profession is the student's chosen "métier visé"; `parcours` is
    resolved server-side (never accepted from the client, §2 scope
    decision). `motivation_text` is optional; when present it must be
    200-500 words (Story 5.5 AC) — a non-empty motivation also gates the
    request into `pending_moderation` server-side (see the service layer)."""

    profession_id = serializers.CharField(max_length=32)
    motivation_text = serializers.CharField(
        max_length=4000, required=False, allow_blank=True, default=""
    )

    def validate_motivation_text(self, value: str) -> str:
        return _validate_motivation_word_count(value)


class EarlyOutreachResubmitSerializer(serializers.Serializer):
    """Story 5.5 — a student correcting a `rejected` motivation. Unlike the
    create serializer, this one is required-non-blank: resubmitting with an
    empty motivation would silently skip moderation, defeating the point of
    the retry."""

    motivation_text = serializers.CharField(max_length=4000, allow_blank=False)

    def validate_motivation_text(self, value: str) -> str:
        return _validate_motivation_word_count(value)


class EarlyOutreachListSerializer(serializers.ModelSerializer):
    """AC4 — flat list for `/mes-envois` (Story 5.9 will enrich). Includes
    `rejection_reason` (Story 5.5) so the front can show why + offer the
    resubmit action without a second call."""

    school_name = serializers.CharField(source="school.name", read_only=True)
    profession_name = serializers.CharField(source="profession.name", read_only=True)

    class Meta:
        model = EarlyOutreachRequest
        fields = [
            "id",
            "school_name",
            "profession_name",
            "status",
            "rejection_reason",
            "created_at",
        ]
        read_only_fields = fields
