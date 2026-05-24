"""Pytest fixtures for audit tests.

`skip_if_sqlite` was promoted to the project-wide `conftest.py`
(`apps/api/conftest.py`) in Story 1.8 T7 so the RLS test suite shares the
same gate without duplication. Pytest auto-discovers it via the parent
conftest; no import needed.
"""

from __future__ import annotations
