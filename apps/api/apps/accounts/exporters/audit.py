"""Audit-trail exporter: every AuditLog where the user is actor or subject.

The hash-chain columns (`prev_hash`, `row_hash`) are intentionally omitted —
they are internal integrity metadata for the audit subsystem (Story 1.13)
and have no meaning for the user receiving the export.
"""

from __future__ import annotations

import io
import json
from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.db.models import Q

from apps.accounts.exporters import ExporterEntry, register_exporter
from apps.audit.models import AuditLog

if TYPE_CHECKING:
    from apps.accounts.models import User


@register_exporter("audit")
def export_audit_log(user: User) -> Iterable[ExporterEntry]:
    """Yield `audit/audit-log.jsonl` — one event per line, chronological ASC.

    Returns an empty iterable when the user has no audit entries (e.g. fresh
    account, or after audit retention cleanup). The export task then simply
    skips the file.
    """
    qs = (
        AuditLog.objects.filter(Q(subject_id=user.id) | Q(actor_id=user.id))
        .order_by("created_at")
    )

    buf = io.BytesIO()
    has_rows = False
    for row in qs.iterator(chunk_size=500):
        has_rows = True
        line = json.dumps(
            {
                "id": row.id,
                "created_at": row.created_at.isoformat(),
                "action": row.action,
                "result": row.result,
                "actor_id": row.actor_id,
                "actor_role": row.actor_role,
                "subject_id": row.subject_id,
                "metadata": row.metadata,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        buf.write(line.encode("utf-8"))
        buf.write(b"\n")

    if not has_rows:
        return

    yield ExporterEntry(
        archive_path="audit/audit-log.jsonl",
        content=buf.getvalue(),
        content_type="application/x-ndjson",
    )
