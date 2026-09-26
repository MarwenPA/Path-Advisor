from rest_framework import serializers


class AdminMilestoneSerializer(serializers.ModelSerializer):
    """Story 9.2 (amendement 8.3) — milestone create/edit payload."""

    class Meta:
        from .models import ParcoursupMilestone

        model = ParcoursupMilestone
        fields = ("kind", "campaign", "date", "notify_days_before")
