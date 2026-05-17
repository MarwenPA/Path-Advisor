"""Pytest fixtures for audit tests.

The thread-local reset autouse fixture lives in the project-wide `conftest.py`
(`apps/api/conftest.py`) so it covers tests in other apps that exercise the
audit decorator (e.g. accounts integration tests).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def skip_if_sqlite(db):
    """Mark dependent tests as PostgreSQL-only and skip on SQLite."""
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL (trigger-based immutability).")
