"""Per-entry access history — Story 6.11 ("Voir l'historique d'accès").

Rather than a new tracking model, this reads the `AuditLog` rows that
`get_child_professions`-adjacent view services already write on every
profile read (`parent.child_dashboard_viewed`,
`establishments.counselor_profile_viewed`) — the same rows Story 6.8/prior
parent stories already produce, just windowed to 90 days and filtered to
one entry's viewer.

Scope decision: a `ParentalConsent` row created before the viewing parent
had a Path-Advisor account (`parent_user_id IS NULL` — an anonymous
token-based decision, ADR-0003) has no way to be matched to any
`AuditLog.actor_id`, so its history is legitimately empty, not a bug.
"""

from __future__ import annotations

import csv
import io
from datetime import timedelta
from typing import TYPE_CHECKING

from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.rls import bypass_rls
from apps.establishments.models import CounselorConsent
from apps.profiles.access_list.exceptions import EntryNotFound

if TYPE_CHECKING:
    from apps.accounts.models import User

HISTORY_WINDOW_DAYS = 90

_ACTIONS_BY_SOURCE = {
    "counselor_consent": "establishments.counselor_profile_viewed",
    "parental_consent": "parent.child_dashboard_viewed",
}


def _resolve_viewer_id(*, user: User, source_name: str, source_pk: str) -> str | None:
    if source_name == "counselor_consent":
        with bypass_rls(reason="access_list_history.resolve_counselor"):
            return (
                CounselorConsent.objects.filter(student=user, id=source_pk)
                .values_list("counselor_id", flat=True)
                .first()
            )
    if source_name == "parental_consent":
        from apps.accounts.models import ParentalConsent

        return (
            ParentalConsent.objects.filter(student=user, id=source_pk)
            .values_list("parent_user_id", flat=True)
            .first()
        )
    return None


def get_access_history(*, user: User, entry_id: str) -> list[dict]:
    """Returns up to 90 days of timestamped consultations for one entry,
    most recent first. Raises `EntryNotFound` for a malformed/unknown id."""
    try:
        source_name, source_pk = entry_id.split(":", 1)
    except ValueError as exc:
        raise EntryNotFound(f"malformed entry id {entry_id!r}") from exc

    action = _ACTIONS_BY_SOURCE.get(source_name)
    if action is None:
        raise EntryNotFound(f"unknown source {source_name!r}")

    viewer_id = _resolve_viewer_id(user=user, source_name=source_name, source_pk=source_pk)
    if not viewer_id:
        return []

    since = timezone.now() - timedelta(days=HISTORY_WINDOW_DAYS)
    with bypass_rls(reason="access_list_history.read_audit_log"):
        rows = AuditLog.objects.filter(
            action=action,
            actor_id=viewer_id,
            subject_id=user.id,
            created_at__gte=since,
        ).order_by("-created_at")
        return [{"consulted_at": row.created_at, "metadata": row.metadata} for row in rows]


def export_access_history_csv(*, user: User, entry_id: str) -> bytes:
    history = get_access_history(user=user, entry_id=entry_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date de consultation", "Données consultées"])
    for row in history:
        writer.writerow([row["consulted_at"].strftime("%d/%m/%Y %H:%M"), row["metadata"]])
    return buffer.getvalue().encode("utf-8")
