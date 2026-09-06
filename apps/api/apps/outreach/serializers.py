"""Serializers for early-outreach requests — Stories 5.4 + 5.5 + 5.6 + 5.7."""

from __future__ import annotations

from datetime import date

from rest_framework import serializers

from apps.outreach.models import (
    EarlyOutreachRequest,
    EarlyOutreachResponse,
    EarlyOutreachResponseAction,
)

COMMENT_MAX_WORDS = 200
MIN_INTERVIEW_SLOTS = 2
MAX_INTERVIEW_SLOTS = 3

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
    """AC4 — flat list for `/mes-envois` (Story 5.9 groups it client-side by
    status/action). Includes `rejection_reason` (Story 5.5) so the front
    can show why + offer the resubmit action without a second call.
    Story 5.7 adds `response` — `null` until the school answers. Story 5.9
    adds `school_slug` — the "lien vers la fiche école" AC."""

    school_name = serializers.CharField(source="school.name", read_only=True)
    school_slug = serializers.CharField(source="school.slug", read_only=True)
    profession_name = serializers.CharField(source="profession.name", read_only=True)
    response = serializers.SerializerMethodField()

    class Meta:
        model = EarlyOutreachRequest
        fields = [
            "id",
            "school_name",
            "school_slug",
            "profession_name",
            "status",
            "rejection_reason",
            "response",
            "created_at",
        ]
        read_only_fields = fields

    def get_response(self, obj: EarlyOutreachRequest) -> dict | None:
        response = getattr(obj, "response", None)
        if response is None:
            return None
        return EarlyOutreachResponseSerializer(response).data


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


class EarlyOutreachResponseSerializer(serializers.ModelSerializer):
    """Story 5.7 — read-only view of a school's response, nested wherever
    a request is displayed (school detail, student list/detail). Story 5.8
    adds `stat_delta` — the exact point value already applied to the
    student's `AdmissionStat` for this school (looked up from the same
    `OUTREACH_RESPONSE_STAT_DELTAS` mapping the propagation service uses,
    single-sourced — never recomputed independently here)."""

    stat_delta = serializers.SerializerMethodField()

    class Meta:
        model = EarlyOutreachResponse
        fields = [
            "action",
            "comment",
            "proposed_slots",
            "accepted_slot",
            "alternative_note",
            "stat_delta",
            "created_at",
        ]
        read_only_fields = fields

    def get_stat_delta(self, obj: EarlyOutreachResponse) -> int:
        from apps.schools.services import OUTREACH_RESPONSE_STAT_DELTAS

        return OUTREACH_RESPONSE_STAT_DELTAS.get(obj.action, 0)


class EcoleOutreachDetailSerializer(EcoleOutreachListSerializer):
    """Story 5.6 AC — fiche détail: same fields + `motivation_text` +
    (Story 5.7) the response, once one exists."""

    response = EarlyOutreachResponseSerializer(read_only=True)

    class Meta(EcoleOutreachListSerializer.Meta):
        fields = [*EcoleOutreachListSerializer.Meta.fields, "motivation_text", "response"]
        read_only_fields = fields


class EarlyOutreachRespondSerializer(serializers.Serializer):
    """Story 5.7 AC — the school's one-shot response form.

    `comment` (≤200 words, no minimum) is the "Commentaire pour l'élève"
    — §2 scope decision: not gated through Story 5.5's a-priori moderation
    queue (see `EarlyOutreachResponse`'s docstring for why).
    `proposed_slots` is required (2-3 ISO-8601 datetimes) only when
    `action=interview_requested`, and must be empty otherwise — a
    non-interview response proposing slots would be a UI bug, not silently
    ignored data.
    """

    action = serializers.ChoiceField(choices=EarlyOutreachResponseAction.choices)
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    proposed_slots = serializers.ListField(
        child=serializers.CharField(max_length=40), required=False, default=list
    )

    def validate_comment(self, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            return value
        word_count = len(stripped.split())
        if word_count > COMMENT_MAX_WORDS:
            raise serializers.ValidationError(
                f"Ton commentaire doit faire au plus {COMMENT_MAX_WORDS} mots "
                f"(actuellement {word_count})."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        action = attrs.get("action")
        slots = attrs.get("proposed_slots") or []
        if action == EarlyOutreachResponseAction.INTERVIEW_REQUESTED:
            if not (MIN_INTERVIEW_SLOTS <= len(slots) <= MAX_INTERVIEW_SLOTS):
                raise serializers.ValidationError(
                    {
                        "proposed_slots": (
                            f"Propose entre {MIN_INTERVIEW_SLOTS} et "
                            f"{MAX_INTERVIEW_SLOTS} créneaux."
                        )
                    }
                )
        elif slots:
            raise serializers.ValidationError(
                {"proposed_slots": "Uniquement pour une demande d'entretien."}
            )
        return attrs


class InterviewAcceptSerializer(serializers.Serializer):
    """Story 5.7 — student accepts one of the school's proposed slots."""

    slot = serializers.CharField(max_length=40)


class InterviewAlternativeSerializer(serializers.Serializer):
    """Story 5.7 — student can't make any proposed slot, suggests one."""

    note = serializers.CharField(max_length=2000, allow_blank=False)


class EarlyOutreachStudentDetailSerializer(EarlyOutreachListSerializer):
    """Story 5.9 AC — fiche détail sur `/mes-envois/{id}`: same fields as
    the list row + the motivation the student sent (not shown in the flat
    list — one extra field the student doesn't need to re-read every
    time)."""

    class Meta(EarlyOutreachListSerializer.Meta):
        fields = [*EarlyOutreachListSerializer.Meta.fields, "motivation_text"]
        read_only_fields = fields
