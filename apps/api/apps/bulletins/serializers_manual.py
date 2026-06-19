"""Serializers for Story 2.4 — BulletinManual POST + PATCH."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from .models import BulletinManual


class MatiereSerializer(serializers.Serializer):
    subject_id = serializers.CharField(max_length=100)
    note = serializers.DecimalField(
        max_digits=4, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("20")
    )
    appreciation = serializers.CharField(max_length=500, allow_null=True, required=False, default=None)
    is_custom = serializers.BooleanField(required=False, default=False)

    def validate_subject_id(self, value: str) -> str:
        if value.startswith("custom:"):
            return value
        return value

    def validate_note(self, value: Decimal) -> Decimal:
        # min_value/max_value on the field already rejects out-of-range;
        # only truncation to 2 decimal places is needed here.
        return round(value, 2)


class BulletinManualCreateSerializer(serializers.ModelSerializer):
    matieres = MatiereSerializer(many=True)

    class Meta:
        model = BulletinManual
        fields = [
            "id",
            "trimestre_label",
            "year",
            "level_at_save",
            "subjects_ref_version",
            "matieres",
            "source",
            "validated_at",
            "created_at",
        ]
        read_only_fields = ["id", "source", "validated_at", "created_at"]

    def validate_matieres(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("At least one subject is required.")
        for m in value:
            appreciation = m.get("appreciation")
            if appreciation and len(appreciation) > 500:
                raise serializers.ValidationError("Appreciation cannot exceed 500 characters.")
        return value

    def create(self, validated_data: dict) -> BulletinManual:
        matieres_raw = validated_data.pop("matieres")
        matieres = [
            {
                "subject_id": m["subject_id"],
                "note": float(m["note"]),
                "appreciation": m.get("appreciation"),
                "is_custom": m.get("is_custom", False),
            }
            for m in matieres_raw
        ]
        return BulletinManual.objects.create(matieres=matieres, **validated_data)


class BulletinManualPatchSerializer(serializers.ModelSerializer):
    matieres = MatiereSerializer(many=True, required=False)

    class Meta:
        model = BulletinManual
        fields = ["matieres", "trimestre_label", "year", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_matieres(self, value: list) -> list:
        for m in value:
            appreciation = m.get("appreciation")
            if appreciation and len(appreciation) > 500:
                raise serializers.ValidationError("Appreciation cannot exceed 500 characters.")
        return value

    def update(self, instance: BulletinManual, validated_data: dict) -> BulletinManual:
        matieres_raw = validated_data.pop("matieres", None)
        if matieres_raw is not None:
            instance.matieres = [
                {
                    "subject_id": m["subject_id"],
                    "note": float(m["note"]),
                    "appreciation": m.get("appreciation"),
                    "is_custom": m.get("is_custom", False),
                }
                for m in matieres_raw
            ]
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
