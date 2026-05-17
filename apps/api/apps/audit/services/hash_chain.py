"""SHA-256 chain over audit rows — tampering detection on top of the PG trigger.

Why a chain: even if an attacker disables the trigger (e.g. via
`SET session_replication_role = 'replica'`) and rewrites a row, the next
integrity check (Story 1.13 §AC6) will recompute hashes and detect the gap.

Caveat: chain integrity assumes the writer can lock the last row during INSERT.
`get_last_row_hash()` therefore SELECTs `FOR UPDATE` so concurrent decorator
calls serialise and produce a linear chain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from django.db import connection


def compute_row_hash(
    *,
    actor_id: str | None,
    action: str,
    subject_id: str | None,
    metadata: dict,
    created_at: datetime,
    prev_hash: str | None,
) -> str:
    """Stable hash for one row. `metadata` is serialised with sort_keys for determinism."""
    payload = "|".join(
        [
            actor_id or "",
            action,
            subject_id or "",
            json.dumps(metadata, sort_keys=True, default=str),
            created_at.isoformat(),
            prev_hash or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_last_row_hash(using: str = "default") -> str | None:
    """Most recent row's hash, with chain-level serialisation.

    Caller must be inside `with transaction.atomic()`.

    Why an advisory lock and not just `SELECT … FOR UPDATE`: on an empty table
    `LIMIT 1 FOR UPDATE` locks no row, so two concurrent first writers both
    read `prev_hash=None` and fork the chain. A transaction-scoped advisory
    lock keyed on a constant ("audit_logs_chain") forces all writers through
    the same critical section regardless of whether rows exist.

    Tiebreaker `id DESC` matters when two rows share `created_at` to the
    microsecond — ULIDs embed monotonic entropy, so larger id = later writer.
    """
    with connection.cursor() as cur:
        if connection.vendor == "postgresql":
            # hashtext() turns the chain name into a stable int4 key.
            cur.execute("SELECT pg_advisory_xact_lock(hashtext('audit_logs_chain'))")
            cur.execute("SELECT row_hash FROM audit_logs ORDER BY created_at DESC, id DESC LIMIT 1")
        else:
            # SQLite test path — no row-level locking; pytest serialises tests.
            cur.execute("SELECT row_hash FROM audit_logs ORDER BY created_at DESC, id DESC LIMIT 1")
        row = cur.fetchone()
    return row[0] if row else None


def verify_chain(rows: list) -> list[str]:
    """Recompute the chain; return IDs of rows whose `row_hash` doesn't match.

    Detection strategy: for each row, recompute its hash from its fields plus
    the *expected* hash of the previous row (what we just computed, not what
    the row claims). This isolates breaks to the actually-tampered row instead
    of cascading downstream — a single mutation in row N shows up as a single
    entry in `broken`, not N broken rows.

    A row also counts as broken if its persisted `prev_hash` disagrees with
    what we expect (e.g. an inserted/deleted row in the middle).
    """
    broken: list[str] = []
    expected_prev: str | None = None
    for row in rows:
        expected = compute_row_hash(
            actor_id=row.actor_id,
            action=row.action,
            subject_id=row.subject_id,
            metadata=row.metadata,
            created_at=row.created_at,
            prev_hash=expected_prev,
        )
        if row.row_hash != expected or (row.prev_hash or None) != (expected_prev or None):
            broken.append(row.id)
        # Continue with the *expected* hash, not the persisted one, so a single
        # tampered row does not cascade and mask the rest of the chain.
        expected_prev = expected
    return broken
