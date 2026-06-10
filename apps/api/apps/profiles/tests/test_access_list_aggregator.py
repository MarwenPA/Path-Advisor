"""``AccessListAggregator`` unit tests — Story 1.9 §T4.4.

Uses fake sources so each test cases targets one aggregator concern (empty,
single, multi, sort, exception isolation, truncation) without touching the
DB or the live registry.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from apps.profiles.access_list import AccessListAggregator, AccessListEntry


def _entry(tier_type: str = "parent", granted_at: datetime | None = None) -> AccessListEntry:
    return AccessListEntry(
        id=f"{tier_type}:{(granted_at or datetime(2026, 1, 1, tzinfo=UTC)).isoformat()}",
        tier_type=tier_type,  # type: ignore[arg-type]
        display_name="x@example.test",
        granted_at=granted_at or datetime(2026, 1, 1, tzinfo=UTC),
        visible_data=("metiers_explores",),
        masked_data=("bulletins_detailles",),
        revocable=True,
        source_name=tier_type,
        source_pk="x",
    )


class _FakeSource:
    def __init__(self, name: str, entries: list[AccessListEntry]) -> None:
        self.name = name
        self._entries = entries

    def list_for_user(self, user):
        return list(self._entries)

    def revoke(self, user, source_pk):
        raise NotImplementedError


def test_empty_when_no_sources_registered():
    agg = AccessListAggregator(sources=[])
    assert agg.list_for_user(Mock()) == []


def test_single_source_happy_path():
    e = _entry()
    agg = AccessListAggregator(sources=[_FakeSource("parental_consent", [e])])
    assert agg.list_for_user(Mock()) == [e]


def test_multi_source_concatenated_and_sorted_by_granted_at_desc():
    older = _entry(granted_at=datetime(2025, 1, 1, tzinfo=UTC))
    newer = _entry(tier_type="school", granted_at=datetime(2026, 6, 1, tzinfo=UTC))
    agg = AccessListAggregator(
        sources=[
            _FakeSource("parental_consent", [older]),
            _FakeSource("school", [newer]),
        ]
    )
    assert agg.list_for_user(Mock()) == [newer, older]


def test_broken_source_does_not_block_other_sources(caplog):
    """One source raising MUST NOT lose the entries of the others."""

    class _BrokenSource:
        name = "broken"

        def list_for_user(self, user):
            raise RuntimeError("simulated DB outage")

        def revoke(self, user, source_pk):
            raise NotImplementedError

    good = _entry()
    agg = AccessListAggregator(sources=[_BrokenSource(), _FakeSource("parental_consent", [good])])
    with caplog.at_level("ERROR"):
        result = agg.list_for_user(Mock())
    assert result == [good]
    assert any("access_list source raised" in m for m in caplog.messages)


def test_truncation_at_max_entries():
    """100-entry cap (§AC8). 101st entry must be dropped."""
    many = [_entry(granted_at=datetime(2026, 1, 1, n % 24, n % 60, tzinfo=UTC)) for n in range(150)]
    agg = AccessListAggregator(sources=[_FakeSource("many", many)])
    assert len(agg.list_for_user(Mock())) == 100


@pytest.mark.django_db
def test_aggregator_with_live_registry_does_not_crash():
    """Smoke test against the actual registered sources (just `parental_consent`)."""
    agg = AccessListAggregator()
    fake_user = Mock(id=1)
    assert agg.list_for_user(fake_user) == []  # No data in fresh DB
