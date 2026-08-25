from __future__ import annotations

from rest_framework import serializers

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
