"""``AccessListSource`` Protocol — Story 1.9 §AC2 extension contract.

A source adapter is the only seam Stories 5.4 (école) and 6.7 (conseillère)
touch to extend the unified list. Implement this protocol + register the
instance in ``apps/profiles/apps.py::ProfilesConfig.ready()`` and the entries
appear in ``GET /api/v1/profile/access-list/`` automatically. No API change.
No frontend change.

The ``revoke`` method is wired here (not in a separate protocol) so Story 1.10
can dispatch to the right adapter from the id alone — but is a no-op /
``NotImplementedError`` in Story 1.9. The two-story split is intentional ;
this story ships the read surface, 1.10 turns on writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from apps.accounts.models import User

    from .dto import AccessListEntry


@runtime_checkable
class AccessListSource(Protocol):
    """Every access source MUST implement this surface.

    ``name`` is the source identifier embedded in the composite ``id`` field
    of each ``AccessListEntry``. Pick a short ``[a-z_]+`` slug — it becomes
    the URL/JSON prefix and is parsed by Story 1.10's revoke endpoint.
    """

    name: str

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        """Return the third-party access entries this source knows about.

        MUST NOT raise on empty result — return ``[]``. MUST NOT return a
        Django QuerySet — return a materialized ``list`` so the aggregator can
        ``+`` it with other sources of different ORMs / external calls.
        """
        ...

    def revoke(self, user: User, source_pk: str) -> None:
        """Revoke ``source_pk`` for ``user`` (Story 1.10).

        In Story 1.9 this is intentionally inert — raise ``NotImplementedError``.
        """
        ...
