"""``AccessListAggregator`` — Story 1.9 §T4.

Walks every registered ``AccessListSource``, concatenates their results, sorts
the unified list by ``granted_at`` descending and truncates at the documented
cap (§AC8 — 100 entries). One broken source MUST NOT block the others :
exceptions are logged at ERROR with the source name and the source is silently
skipped.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from . import registry
from .dto import AccessListEntry

if TYPE_CHECKING:
    from apps.accounts.models import User

    from .protocols import AccessListSource

logger = logging.getLogger(__name__)

#: §AC8 — pagination is out of scope ; the cap is a deliberate punt. A real
#: student today has ≤ 3 entries ; the cap is a 30x safety margin.
MAX_ENTRIES = 100


class AccessListAggregator:
    def __init__(self, sources: list[AccessListSource] | None = None) -> None:
        # Default to the live registry ; tests pass a custom list.
        self.sources = sources if sources is not None else registry.SOURCES

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        entries: list[AccessListEntry] = []
        for source in self.sources:
            try:
                entries.extend(source.list_for_user(user))
            except Exception:
                logger.exception(
                    "access_list source raised — skipping",
                    extra={"source_name": source.name, "user_id": getattr(user, "id", None)},
                )
        entries.sort(key=lambda e: e.granted_at, reverse=True)
        return entries[:MAX_ENTRIES]
