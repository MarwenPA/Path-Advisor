"""Unified access-list DTO — Story 1.9 §AC1.

A frozen dataclass so source adapters cannot accidentally mutate entries that
another adapter (or the aggregator) might also hold a reference to. The DTO
shape is the API contract — every source MUST produce instances of this
exact type, regardless of its underlying ORM / external service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

#: Source `name` lives both inside the DTO (for routing in Story 1.10) and as
#: the prefix of the composite ``id``. Keep them in sync.
TierType = Literal["parent", "school", "counselor"]


@dataclass(frozen=True, slots=True)
class AccessListEntry:
    """One row in the unified access list.

    The ``id`` field is a composite ``<source_name>:<source_pk>`` string —
    self-routing so the Story 1.10 revoke endpoint can dispatch to the right
    source adapter from the id alone. ``visible_data`` / ``masked_data`` come
    from ``VISIBILITY_MATRIX[tier_type]`` — never inline them in the adapter.
    """

    id: str
    tier_type: TierType
    display_name: str
    granted_at: datetime
    visible_data: tuple[str, ...]
    masked_data: tuple[str, ...]
    revocable: bool
    source_name: str
    source_pk: str
