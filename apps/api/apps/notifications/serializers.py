from rest_framework import serializers


class AdminMilestoneSerializer(serializers.ModelSerializer):
    """Story 9.2 (amendement 8.3) — milestone create/edit payload."""

    class Meta:
        from .models import ParcoursupMilestone

        model = ParcoursupMilestone
        fields = ("kind", "campaign", "date", "notify_days_before")


class _PushKeysSerializer(serializers.Serializer):
    """`PushSubscription.toJSON().keys` — base64url strings, opaque to us."""

    p256dh = serializers.CharField(max_length=255)
    auth = serializers.CharField(max_length=255)


class PushSubscriptionSerializer(serializers.Serializer):
    """Story 10.2 — the browser subscription payload, as the Push API emits it."""

    endpoint = serializers.URLField(max_length=2000)
    keys = _PushKeysSerializer()
