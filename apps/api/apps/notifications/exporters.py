"""GDPR Art. 15/20 exporter for the Epic 8 notification data.

Revue Epic 8 (P3): `notification_preferences` and `delta_recap_cursors`
qualify as personal data by their own docstrings but were missing from the
Story 1.11 export. Auto-loaded by `AccountsConfig.ready()`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TYPE_CHECKING

from apps.accounts.exporters import ExporterEntry, register_exporter

if TYPE_CHECKING:
    from apps.accounts.models import User


@register_exporter("notifications")
def export_notifications(user: User) -> Iterable[ExporterEntry]:
    """Preference rows (opt-out model: absence = enabled) + the DeltaRecap
    cursor (when the student last consumed their recap)."""
    from .models import DeltaRecapCursor, NotificationCategory, NotificationPreference

    rows = {
        p.category: {"enabled": p.enabled, "updated_at": p.updated_at.isoformat()}
        for p in NotificationPreference.objects.filter(user_id=user.pk)
    }
    payload: dict[str, object] = {
        "preferences": [
            {
                "category": value,
                "label": label,
                # Opt-out model — a category without a row is enabled.
                **rows.get(value, {"enabled": True, "updated_at": None}),
            }
            for value, label in NotificationCategory.choices
        ],
    }
    cursor = DeltaRecapCursor.objects.filter(user_id=user.pk).first()
    payload["delta_recap_seen_at"] = cursor.seen_at.isoformat() if cursor else None

    yield ExporterEntry(
        archive_path="notifications/notifications.json",
        content=json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8"),
        content_type="application/json",
    )
