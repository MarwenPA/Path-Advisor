"""Prefixed ULID helpers — `usr_01HX...`, `cnst_01HX...`, etc.

Convention (implementation-patterns §Data Exchange): every primary identifier
exposed by the API carries a domain prefix so it is self-describing in logs
and URLs. The ULID half ensures sortability + uniqueness.
"""

from __future__ import annotations

from ulid import ULID


def generate_id(prefix: str) -> str:
    """Return `<prefix>_<ulid>` (e.g. `"usr_01HXJ7..."`).

    The prefix MUST be a short, lowercase domain code: `usr`, `cnst`, `req`,
    `sch`, etc. Pick once per entity type and never change — IDs are leaked
    in client storage, logs, and external integrations.
    """
    if not prefix or not prefix.isascii() or "_" in prefix:
        raise ValueError(f"Invalid id prefix: {prefix!r}")
    return f"{prefix}_{ULID()}"
