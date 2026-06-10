"""DRF serializers for ``apps.profiles`` — Story 1.9 §T5.

``AccessListEntrySerializer`` is a plain ``Serializer`` (not ``ModelSerializer``)
because the source is the ``AccessListEntry`` dataclass, not a Django model.
"""

from __future__ import annotations

from rest_framework import serializers


class AccessListEntrySerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    tier_type = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    granted_at = serializers.DateTimeField(read_only=True)
    visible_data = serializers.ListField(child=serializers.CharField(), read_only=True)
    masked_data = serializers.ListField(child=serializers.CharField(), read_only=True)
    revocable = serializers.BooleanField(read_only=True)
