"""Serializers for bulletin upload, OCR status, and finalize endpoints."""

from __future__ import annotations

import mimetypes

from django.conf import settings
from rest_framework import serializers

from apps.bulletins.models import Bulletin, BulletinOCRJob, OCRJobStatus

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/heic",
    "image/heif",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_FILES_PER_UPLOAD = 6


class BulletinUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        if file.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Trop gros : ce fichier fait {file.size // (1024 * 1024)} MB, max 10 MB."
            )
        mime = file.content_type or mimetypes.guess_type(file.name)[0] or ""
        if mime not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"Format non accepté : {mime}. Acceptés : PDF, JPEG, PNG, HEIC."
            )
        return file


class BulletinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bulletin
        fields = [
            "id",
            "original_filename",
            "file_size_bytes",
            "mime_type",
            "uploaded_status",
            "uploaded_at",
            "validated_at",
        ]
        read_only_fields = fields


class OCRStartSerializer(serializers.Serializer):
    bulletin_ids = serializers.ListField(
        child=serializers.CharField(max_length=32),
        min_length=1,
        max_length=MAX_FILES_PER_UPLOAD,
    )

    def validate_bulletin_ids(self, ids):
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Duplicate bulletin IDs.")
        return ids


class OCRStatusSerializer(serializers.Serializer):
    """Response shape for GET /bulletins/ocr/status."""

    job_id = serializers.CharField()
    status = serializers.ChoiceField(choices=OCRJobStatus.choices)
    estimated_seconds = serializers.IntegerField(read_only=True)
    extraction = serializers.JSONField(allow_null=True, read_only=True)
    error = serializers.CharField(allow_null=True, read_only=True)


class BulletinFinalizeFieldSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField(allow_blank=True)
    confidence = serializers.FloatField(required=False, default=1.0)
    unmapped = serializers.BooleanField(required=False, default=False)
    canonical_id = serializers.CharField(required=False, allow_null=True)


class BulletinFinalizeSerializer(serializers.Serializer):
    """PATCH /bulletins/{bulletin_id}/finalize — student-corrected fields."""

    fields = serializers.ListField(
        child=BulletinFinalizeFieldSerializer(),
        allow_empty=False,
    )
    label = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_fields(self, fields_data):
        for field in fields_data:
            if field["key"] == "note":
                try:
                    val = float(field["value"].replace(",", "."))
                except (ValueError, AttributeError):
                    raise serializers.ValidationError(
                        f"Note invalide : '{field['value']}'. Doit être un nombre entre 0 et 20."
                    )
                if not 0 <= val <= 20:
                    raise serializers.ValidationError(
                        f"Note hors limites : {val}. Doit être entre 0 et 20."
                    )
        return fields_data
