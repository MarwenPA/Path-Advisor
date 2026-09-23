"""Story 8.9 — strict ingest validation for anonymous RUM beacons.

The endpoint is `AllowAny` and unauthenticated by design, which makes it a
junk-flood target: every field is a closed enum and `value` is hard-bounded,
so garbage costs the sender a request and costs us nothing but a 400.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import RumConnection, RumDevice, RumMetric, RumPageType, RumRating, RumVital

#: One page load emits at most 5 metrics (LCP, CLS, INP, TTFB, FCP); a batch
#: bigger than that is not a browser, it's a script.
MAX_BATCH = 10

#: 2 minutes. No legitimate vital exceeds this; CLS (unitless, typically <1)
#: fits trivially under it.
MAX_VALUE = 120_000.0


class RumVitalSerializer(serializers.ModelSerializer):
    metric = serializers.ChoiceField(choices=RumMetric.choices)
    rating = serializers.ChoiceField(choices=RumRating.choices)
    page_type = serializers.ChoiceField(choices=RumPageType.choices)
    device = serializers.ChoiceField(choices=RumDevice.choices)
    connection = serializers.ChoiceField(
        choices=RumConnection.choices, default=RumConnection.UNKNOWN
    )
    value = serializers.FloatField(min_value=0.0, max_value=MAX_VALUE)

    class Meta:
        model = RumVital
        fields = ["metric", "value", "rating", "page_type", "device", "connection"]


class RumIngestSerializer(serializers.Serializer):
    """Envelope: `{"vitals": [...]}` — one beacon per page view, batched."""

    # DRF's ListSerializer honors max_length at runtime (pinned by
    # test_oversized_batch_rejected); the djangorestframework-stubs signature
    # lags behind, hence the targeted ignore.
    vitals = RumVitalSerializer(  # type: ignore[call-arg]
        many=True, allow_empty=False, max_length=MAX_BATCH
    )

    def create(self, validated_data: dict) -> list[RumVital]:
        rows = [RumVital(**item) for item in validated_data["vitals"]]
        return RumVital.objects.bulk_create(rows)
