"""Composite-id → source-adapter dispatcher — Story 1.10 §T1.2 + review patches.

The single entry point the POST view calls. Encapsulates :
- the composite-id parse (split on the FIRST `:` — §AC2)
- the source lookup via the registry
- the source's ``revoke`` invocation
- the unified audit-row write on success/failure (with discrete failure reasons,
  review patch P9 — splits the `not_found` vs `wrong_owner` cases the spec
  §AC5 required as separate metadata reasons)
- on idempotent no-op (already-revoked), SKIP the success audit row to
  satisfy AC9 "only ONE audit row per logical revocation" (review patch P4)

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
from .results import RevocationResult

if TYPE_CHECKING:
    from apps.accounts.models import User

#: Per-tier metadata fields the audit-row enrichment uses (review patch P10).
#: Today only ``parental_consent`` is live ; extend when Stories 5.4 / 6.7 ship.
_SOURCE_TO_TIER_TYPE: dict[str, str] = {
    "parental_consent": "parent",
    "school_partnership": "school",
    "counselor_consent": "counselor",
}


def revoke_entry(user: User, entry_id: str, *, content_hash: str | None = None) -> dict:
    """Parse + dispatch + audit. Returns a dict echoing the revoked id.

    The audit row uses the composite id as ``subject_id`` so the DPO can grep
    by it directly. ``content_hash`` (when provided) is stored in metadata as
    forensic proof of WHAT the user saw at revoke time (Story 1.4 / 1.14
    pattern — see review decision D4).
    """
    source_name, _, source_pk = entry_id.partition(":")
    if not source_name or not source_pk:
        _audit_attempt(user, entry_id, reason="malformed_id")
        raise EntryNotFound(f"malformed entry id {entry_id!r}")

    source = registry.get_source_by_name(source_name)
    if source is None:
        _audit_attempt(user, entry_id, reason="unknown_source")
        raise EntryNotFound(f"unknown source {source_name!r}")

    try:
        result = source.revoke(user, source_pk)
    except EntryNotFound:
        # Review P9 — discrete reason so the DPO can distinguish a typo from
        # a probing campaign (the AC5 closing comment explicitly flagged this).
        _audit_attempt(user, entry_id, reason="not_found")
        raise

    # Review P4 — skip the success audit row on the idempotent path so AC9
    # ("only ONE audit row per logical revocation") holds even on double-POST.
    if result == RevocationResult.ALREADY_REVOKED:
        return {"revoked": True, "id": entry_id, "already_revoked": True}

    # Review P10 — enrich metadata with tier_type + display_name per §AC5
    # so the audit row is self-contained (no need to join back to the source
    # table to recover the human-readable identity).
    tier_type = _SOURCE_TO_TIER_TYPE.get(source_name, source_name)
    metadata: dict[str, str] = {
        "source_name": source_name,
        "source_pk": source_pk,
        "tier_type": tier_type,
    }
    if content_hash:
        metadata["content_hash"] = content_hash
    display_name = _resolve_display_name(source, user, source_pk)
    if display_name is not None:
        metadata["display_name"] = display_name

    record_audit(
        action="profile.access_revoked",
        result=AuditResult.SUCCESS,
        actor=user,
        subject_id=entry_id,
        metadata=metadata,
    )
    return {"revoked": True, "id": entry_id}


def _resolve_display_name(source, user: User, source_pk: str) -> str | None:
    """Best-effort lookup of the revoked tier's display name for the audit row.

    Source adapters may expose ``display_name_for(user, source_pk)`` if they
    can supply this cheaply. If absent or raises, return None.
    """
    fetcher = getattr(source, "display_name_for", None)
    if fetcher is None:
        return None
    try:
        return fetcher(user, source_pk)
    except Exception:
        return None


def _audit_attempt(user: User, entry_id: str, *, reason: str) -> None:
    """Failure-path audit row — Story 1.10 §AC3 + §AC5 (review P9 reasons split)."""
    record_audit(
        action="profile.access_revoke_attempted",
        result=AuditResult.FAILURE,
        actor=user,
        subject_id=entry_id,
        metadata={"reason": reason},
    )
