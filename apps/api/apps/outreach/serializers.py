"""Serializers for early-outreach requests — Story 5.4."""

from __future__ import annotations

from rest_framework import serializers

from apps.outreach.models import EarlyOutreachRequest


class EarlyOutreachCreateSerializer(serializers.Serializer):
    """AC2 — profession is the student's chosen "métier visé"; `parcours` is
    resolved server-side (never accepted from the client, §2 scope
    decision). `motivation_text` is optional (0-500 words; the 200-word
    floor from the epic spec is a UX nudge, not enforced server-side in
    this story — Story 5.5 owns the real moderation/validation gate)."""

    profession_id = serializers.CharField(max_length=32)
    motivation_text = serializers.CharField(
        max_length=4000, required=False, allow_blank=True, default=""
    )


class EarlyOutreachListSerializer(serializers.ModelSerializer):
    """AC4 — flat list for `/mes-envois` (Story 5.9 will enrich)."""

    school_name = serializers.CharField(source="school.name", read_only=True)
    profession_name = serializers.CharField(source="profession.name", read_only=True)

    class Meta:
        model = EarlyOutreachRequest
        fields = [
            "id",
            "school_name",
            "profession_name",
            "status",
            "created_at",
        ]
        read_only_fields = fields
