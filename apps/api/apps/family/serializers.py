from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import UserRole
from apps.family.models import ParentInvitation, ParentRelationship


class ParentInvitationCreateSerializer(serializers.Serializer):
    parent_email = serializers.EmailField()
    relationship = serializers.ChoiceField(
        choices=ParentRelationship.choices, required=False, allow_null=True
    )
    custom_message = serializers.CharField(
        max_length=200, required=False, allow_null=True, allow_blank=True
    )


class ParentInvitationListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentInvitation
        fields = [
            "id",
            "parent_email",
            "relationship",
            "custom_message",
            "status",
            "created_at",
            "expires_at",
            "accepted_at",
        ]


class ParentInvitationPublicSerializer(serializers.Serializer):
    student_first_name = serializers.CharField()
    student_masked_email = serializers.CharField()
    # Story 6.1 scope decision: the story §AC3 GET payload spec omits
    # `parent_email`, but AC3 also requires the accept form to pre-fill a
    # non-editable email — the parent's own address, known only from the
    # invitation row. Adding it here (never masked — it's the recipient's
    # own address, not third-party PII) is the only way to satisfy both
    # clauses. Documented in Completion Notes.
    parent_email = serializers.EmailField()
    relationship = serializers.CharField(allow_null=True)
    custom_message = serializers.CharField(allow_null=True)
    status = serializers.CharField()


class ParentInvitationAcceptSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        # Code-review fix (2026-08): `password` was `required=False`
        # unconditionally, so a direct API call omitting it created a
        # `User` with an unusable password (`create_user(password=None)`)
        # — the parent gets auto-logged-in once by `parent_invitation_accept`
        # and then can NEVER log back in; the `ParentStudentLink` becomes
        # orphaned. `password` is only actually optional on the AC4 path
        # (an already-authenticated `role="parent"` user just adds a link —
        # no account is created), so gate the requirement on that context
        # instead of relaxing it for everyone. The view must pass
        # `context={"request": request}` for this check to run.
        request = self.context.get("request")
        is_existing_parent_linking = bool(
            request
            and getattr(request, "user", None)
            and request.user.is_authenticated
            and request.user.role == UserRole.PARENT
        )
        if not is_existing_parent_linking:
            password = attrs.get("password")
            if not password:
                raise serializers.ValidationError(
                    {"password": ["Ce champ est requis pour créer un compte."]}
                )
            validate_password(password)
        return attrs


# ---------------------------------------------------------------------------
# Story 6.2 — parent read-only dashboard DTOs (schema/documentation only; the
# service returns plain dicts, so these serializers are used for drf-spectacular
# and to make the response shape explicit).
# ---------------------------------------------------------------------------


class LinkedChildSerializer(serializers.Serializer):
    id = serializers.CharField()
    first_name = serializers.CharField()
    masked_email = serializers.CharField()


class ParentProfessionSignalSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()


class ParentProfessionSerializer(serializers.Serializer):
    metier_id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField(allow_null=True)
    score = serializers.IntegerField()
    confidence_level = serializers.CharField()
    signals = ParentProfessionSignalSerializer(many=True)
    phrase_recopiable = serializers.CharField(allow_blank=True)


class ParentMesParisItemSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    city = serializers.CharField()
    type = serializers.CharField()
    tuition_min_eur = serializers.IntegerField(allow_null=True)
    tuition_max_eur = serializers.IntegerField(allow_null=True)


class ParentCostBreakdownItemSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    school_name = serializers.CharField()
    tuition_min_eur = serializers.IntegerField(allow_null=True)
    tuition_max_eur = serializers.IntegerField(allow_null=True)


class ParentCostsSerializer(serializers.Serializer):
    total_min_eur = serializers.IntegerField()
    total_max_eur = serializers.IntegerField()
    count = serializers.IntegerField()
    breakdown = ParentCostBreakdownItemSerializer(many=True)


class ParentChildDashboardSerializer(serializers.Serializer):
    child = LinkedChildSerializer()
    metiers_explores = ParentProfessionSerializer(many=True)
    mes_paris = ParentMesParisItemSerializer(many=True)
    couts_estimes = ParentCostsSerializer()


class ParentMetierDetailSerializer(serializers.Serializer):
    """Story 6.2 AC2 (code review, 2026-08) — dedicated parent métier detail."""

    metier_id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField(allow_null=True)
    description = serializers.CharField()
    daily_routine = serializers.CharField()
    median_salary_eur = serializers.IntegerField(allow_null=True)
    prospects_text = serializers.CharField()
    score = serializers.IntegerField(allow_null=True)
    confidence_level = serializers.CharField(allow_null=True)
    signals = ParentProfessionSignalSerializer(many=True)


class ParentEcoleFormationSerializer(serializers.Serializer):
    name = serializers.CharField()
    duration_years = serializers.IntegerField()
    parcoursup_open = serializers.BooleanField()
    affelnet_open = serializers.BooleanField()


class ParentAdmissionStatSerializer(serializers.Serializer):
    """Story 6.3 §AC3 — every `AdmissionStat` field except `action_lever`
    (deliberately absent: it names a subject + grade delta, indirectly
    revealing a bulletin figure the parent surface otherwise withholds)."""

    min_proba = serializers.IntegerField()
    expected_proba = serializers.IntegerField()
    max_proba = serializers.IntegerField()
    label = serializers.CharField()
    context_line = serializers.CharField()
    previous_proba = serializers.IntegerField(allow_null=True)
    updated_at = serializers.DateTimeField()


class ParentEcoleDetailSerializer(serializers.Serializer):
    """Story 6.2 AC2 (code review, 2026-08) — dedicated parent école detail.
    Story 6.3 adds `admission_stat` (null if the child never generated one
    for this school)."""

    school_id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    city = serializers.CharField()
    region = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    tuition_min_eur = serializers.IntegerField(allow_null=True)
    tuition_max_eur = serializers.IntegerField(allow_null=True)
    formations = ParentEcoleFormationSerializer(many=True)
    admission_stat = ParentAdmissionStatSerializer(allow_null=True)
