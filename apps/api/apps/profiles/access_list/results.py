"""Revocation result sentinel — Story 1.10 review P4.

The source's ``revoke`` returns an enum so the revoker can distinguish
"actually revoked just now" from "was already revoked" — and skip writing
a second ``profile.access_revoked`` audit row on the idempotent path (AC9).
"""

from __future__ import annotations

from enum import StrEnum


class RevocationResult(StrEnum):
    PERFORMED = "performed"  # the row was revoked by THIS call
    ALREADY_REVOKED = "already_revoked"  # idempotent no-op
