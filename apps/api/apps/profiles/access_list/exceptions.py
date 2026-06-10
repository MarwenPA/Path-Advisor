"""Access-list domain exceptions — Story 1.10 §T1.1."""

from __future__ import annotations


class EntryNotFound(Exception):
    """Raised by an ``AccessListSource.revoke`` when the targeted row does not
    exist or is not owned by the calling user.

    The view turns this into a ``404 Not Found`` Problem Details response —
    deliberately not differentiating "doesn't exist" from "wrong owner" so the
    endpoint cannot be used as an oracle to probe other users' grant ids.
    """
