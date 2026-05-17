"""Read-only serialiser for `AuditLog` rows exposed via the DPO endpoints."""

from __future__ import annotations

from typing import ClassVar

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        # Field order intentional: matches the CSV export columns for visual parity.
        fields: ClassVar[list[str]] = [
            "id",
            "created_at",
            "actor_id",
            "actor_role",
            "tenant_id",
            "subject_id",
            "action",
            "result",
            "request_id",
            "ip_address_hash",
            "user_agent",
            "metadata",
            "prev_hash",
            "row_hash",
        ]
        read_only_fields: ClassVar[list[str]] = fields
