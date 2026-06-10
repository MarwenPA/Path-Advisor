"""Access-list module — Story 1.9 §FR8.

Public surface — what other modules import:

- ``AccessListAggregator`` (from ``.aggregator``) — service that walks every
  registered source and returns a unified list of third-party access entries
  for a given user.
- ``AccessListEntry`` (from ``.dto``) — immutable DTO describing one access
  record (parent, school, counselor, ...).
- ``AccessListSource`` (from ``.protocols``) — Protocol every source adapter
  implements. The extension contract for Stories 5.4 (école) + 6.7 (conseillère).
- ``registry`` (module) — module-level list of registered sources + helpers.
- ``VISIBILITY_MATRIX`` (from ``.visibility_matrix``) — single source of truth
  mapping ``TierType`` → ``{visible: list, masked: list}``.

See ``docs/patterns/access-list-aggregator.md`` for the extension recipe.
"""

from .aggregator import AccessListAggregator
from .dto import AccessListEntry
from .protocols import AccessListSource
from .visibility_matrix import VISIBILITY_MATRIX, TierType

__all__ = [
    "VISIBILITY_MATRIX",
    "AccessListAggregator",
    "AccessListEntry",
    "AccessListSource",
    "TierType",
]
