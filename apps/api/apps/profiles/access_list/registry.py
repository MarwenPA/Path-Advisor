"""Module-level source registry — Story 1.9 §AC2.

The registry is a global mutable list (one process, one Django app instance)
populated by ``ProfilesConfig.ready()`` at startup. Reading is lock-free
because ``ready()`` runs once on import — past that point the list is
effectively immutable in normal execution. Tests reset it via
``apps.profiles.access_list.registry.reset()`` in a fixture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .protocols import AccessListSource

SOURCES: list[AccessListSource] = []


def register(source: AccessListSource) -> None:
    """Add ``source`` to the registry. Idempotent — re-registering by name is a no-op."""
    if any(s.name == source.name for s in SOURCES):
        return
    SOURCES.append(source)


def get_source_by_name(name: str) -> AccessListSource | None:
    """Story 1.10 will use this to route a revoke call by composite-id prefix."""
    for source in SOURCES:
        if source.name == name:
            return source
    return None


def reset() -> None:
    """Test-only helper. Clears the registry so a fixture can register fakes."""
    SOURCES.clear()
