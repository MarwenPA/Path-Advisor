"""Composite-id → source-adapter dispatcher — Story 1.10 §T1.2.

The single entry point the POST view calls. Encapsulates :
- the composite-id parse (split on the FIRST `:` — §AC2)
- the source lookup via the registry
- the source's ``revoke`` invocation
- the unified audit-row write on success/failure

Exception envelope :
- ``EntryNotFound`` (from the source adapter or our own "unknown source" path)
  → translated to 404 by the view
- everything else propagates → 500 (logged + Sentry by the global handler)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult

from . import registry
from .exceptions import EntryNotFound

if TYPE_CHECKING:
    from apps.accounts.models import User


def revoke_entry(user: User, entry_id: str, *, content_hash: str | None = None) -> dict:
    """Parse + dispatch + audit. Returns a dict echoing the revoked id.

    The audit row uses the composite id as ``subject_id`` so the DPO can grep
    by it directly without joining to the source table. ``content_hash`` (when
    provided) is stored in metadata as forensic proof of WHAT the user saw at
    revoke time (Story 1.14 / Story 1.4 pattern).
    """
    source_name, _, source_pk = entry_id.partition(":")
    if not source_name or not source_pk:
        # Malformed id → same UX as "not found" per §AC2.
        _audit_attempt(user, entry_id, reason="malformed_id")
        raise EntryNotFound(f"malformed entry id {entry_id!r}")

    source = registry.get_source_by_name(source_name)
    if source is None:
        # Unknown source name → also 404 per §AC1 (student doesn't need to
        # know whether the source is missing or the row is missing).
        _audit_attempt(user, entry_id, reason="unknown_source")
        raise EntryNotFound(f"unknown source {source_name!r}")

    try:
        source.revoke(user, source_pk)
    except EntryNotFound:
        _audit_attempt(user, entry_id, reason="not_found_or_wrong_owner")
        raise

    metadata: dict[str, str] = {"source_name": source_name, "source_pk": source_pk}
    if content_hash:
        metadata["content_hash"] = content_hash
    record_audit(
        action="profile.access_revoked",
        result=AuditResult.SUCCESS,
        actor=user,
        subject_id=entry_id,
        metadata=metadata,
    )
    return {"revoked": True, "id": entry_id}


def _audit_attempt(user: User, entry_id: str, *, reason: str) -> None:
    """Failure-path audit row — Story 1.10 §AC3 + §AC5."""
    record_audit(
        action="profile.access_revoke_attempted",
        result=AuditResult.FAILURE,
        actor=user,
        subject_id=entry_id,
        metadata={"reason": reason},
    )
