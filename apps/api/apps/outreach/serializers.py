"""Serializers for early-outreach requests — Stories 5.4 + 5.5 + 5.6."""

from __future__ import annotations

from datetime import date

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


def _student_age(student) -> int | None:
    """A student's age is the one "profil scolaire synthétique" datum this
    story can build without new work — a full synthesis of bulletins/niveau
    (Epic 2/4 territory) is explicitly out of scope for 5.6. No name, no
    email: NFR-S4 keeps identity minimal on the school side."""
    if not student.birth_date:
        return None
    today = date.today()
    return (
        today.year
        - student.birth_date.year
        - ((today.month, today.day) < (student.birth_date.month, student.birth_date.day))
    )


class EcoleOutreachListSerializer(serializers.ModelSerializer):
    """Story 5.6 AC — reception queue row. Deliberately does NOT expose
    `student.email` or any name (the User model has none anyway) — only
    what's needed to triage: age, métier visé, parcours, date, status.
    `student_age` intentionally NOT `student_id`/`student` — leaking the
    student's internal id would let a curious school admin correlate rows
    across schools, defeating the "no other schools" boundary in spirit."""

    profession_name = serializers.CharField(source="profession.name", read_only=True)
    parcours_label = serializers.CharField(source="parcours.label", read_only=True, default=None)
    student_age = serializers.SerializerMethodField()

    class Meta:
        model = EarlyOutreachRequest
        fields = [
            "id",
            "student_age",
            "profession_name",
            "parcours_label",
            "status",
            "created_at",
        ]
        read_only_fields = fields

    def get_student_age(self, obj: EarlyOutreachRequest) -> int | None:
        return _student_age(obj.student)


class EcoleOutreachDetailSerializer(EcoleOutreachListSerializer):
    """Story 5.6 AC — fiche détail: same fields + `motivation_text`."""

    class Meta(EcoleOutreachListSerializer.Meta):
        fields = [*EcoleOutreachListSerializer.Meta.fields, "motivation_text"]
        read_only_fields = fields
