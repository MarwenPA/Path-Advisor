"""Project-wide pytest fixtures.

Anything cross-cutting that test files in any app would otherwise duplicate
lives here. App-specific helpers stay in their own `apps/<app>/tests/conftest.py`.
"""

from __future__ import annotations

import pytest

from apps.core import request_context


@pytest.fixture(autouse=True)
def _audit_request_context_isolation():
    """Reset the audit thread-local around every test.

    The audit decorator reads actor/tenant/ip from a thread-local. Without
    this fixture, leaked state from a previous test (especially under
    pytest-xdist worker thread reuse) would taint subsequent audit rows
    with the wrong actor.
    """
    request_context.clear()
    yield
    request_context.clear()
