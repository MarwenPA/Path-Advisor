"""``AccessListAggregator`` — Story 1.9 §T4 + review patches D3 P5.

Walks every registered ``AccessListSource``, concatenates their results, sorts
the unified list by ``granted_at`` descending and truncates at the documented
cap (§AC8 — 100 entries).

Review D3 — narrowed the source-isolation `except` to actual transient/IO
errors (``DatabaseError``, ``ConnectionError``, ``TimeoutError``). Programming
errors (``AttributeError``, ``KeyError``, ``TypeError``) bubble up to a 500
so they surface in Sentry instead of silently returning partial lists.

Review P5 — defensive sort key handles ``granted_at=None`` (a future source
adapter might forget to filter — don't let it crash the whole aggregator).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from django.db import DatabaseError

from . import registry
from .dto import AccessListEntry

if TYPE_CHECKING:
    from apps.accounts.models import User

    from .protocols import AccessListSource

logger = logging.getLogger(__name__)

#: §AC8 — pagination is out of scope ; the cap is a deliberate punt. A real
#: student today has ≤ 3 entries ; the cap is a 30x safety margin.
MAX_ENTRIES = 100

#: §AC8 second clause (review patch P7) — emitted in the response when the
#: result was capped. Frontend can use this to surface "truncated" UI later.
TRUNCATED_FLAG_KEY = "truncated"

#: Transient/IO errors a source might raise that should NOT block other sources.
#: Programming bugs (AttributeError, TypeError, KeyError, ValueError) are
#: deliberately NOT in this tuple — they should 500 so Sentry catches them.
_TRANSIENT_SOURCE_ERRORS = (DatabaseError, ConnectionError, TimeoutError, OSError)


class AccessListAggregator:
    def __init__(self, sources: list[AccessListSource] | None = None) -> None:
        # Default to the live registry ; tests pass a custom list.
        self.sources = sources if sources is not None else registry.SOURCES

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        entries: list[AccessListEntry] = []
        for source in self.sources:
            try:
                entries.extend(source.list_for_user(user))
            except _TRANSIENT_SOURCE_ERRORS:
                logger.exception(
                    "access_list source raised transient error — skipping",
                    extra={"source_name": source.name, "user_id": getattr(user, "id", None)},
                )
        entries.sort(key=_sort_key, reverse=True)
        return entries[:MAX_ENTRIES]


def _sort_key(entry: AccessListEntry) -> datetime:
    """Review P5 — defensive : a source returning ``granted_at=None`` would
    crash the sort. Treat None as the epoch (sinks to the bottom of a
    descending sort, which is the right place for "unknown timestamp").
    """
    return entry.granted_at or datetime(1, 1, 1, tzinfo=UTC)
