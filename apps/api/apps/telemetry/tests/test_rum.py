"""Story 8.9 — RUM ingest + summary endpoint tests.

Ingest is the app's only unauthenticated WRITE surface, so the validation
tests double as the abuse-surface spec: closed enums, bounded values,
bounded batch, per-IP throttle. The summary tests pin the p75 math
(nearest-rank) and the path_admin-only read.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.core.rls_testing import as_path_admin
from apps.telemetry.models import RumVital
from apps.telemetry.views import _p75

INGEST_URL = "/api/v1/rum/vitals/"
SUMMARY_URL = "/api/v1/admin/rum/summary/"


def _vital(**overrides) -> dict:
    base = {
        "metric": "LCP",
        "value": 2100.5,
        "rating": "good",
        "page_type": "metier_fiche",
        "device": "mobile",
        "connection": "4g",
    }
    return {**base, **overrides}


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def student_client(db):
    with as_path_admin():
        user = User.objects.create_user(
            email="eleve-rum@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(db):
    with as_path_admin():
        user = User.objects.create_user(
            email="admin-rum@test.local",
            password="Strong1!pass",
            role=UserRole.PATH_ADMIN,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            is_superuser=True,
        )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRumIngest:
    def test_anonymous_batch_is_stored(self, anon_client):
        payload = {"vitals": [_vital(), _vital(metric="CLS", value=0.04)]}
        resp = anon_client.post(INGEST_URL, payload, format="json")
        assert resp.status_code == 204
        assert RumVital.objects.count() == 2
        row = RumVital.objects.get(metric="LCP")
        assert row.page_type == "metier_fiche"
        assert row.device == "mobile"

    def test_no_personal_data_is_storable(self, anon_client):
        """Privacy by construction: the model has no user/IP/URL column."""
        field_names = {f.name for f in RumVital._meta.get_fields()}
        assert field_names == {
            "id",
            "metric",
            "value",
            "rating",
            "page_type",
            "device",
            "connection",
            "created_at",
        }

    def test_unknown_page_type_rejected(self, anon_client):
        # `page_type` is a closed enum — a raw pathname must never slip in
        # (a slug could identify a niche interest; a page type cannot).
        resp = anon_client.post(
            INGEST_URL, {"vitals": [_vital(page_type="/metiers/foo")]}, format="json"
        )
        assert resp.status_code == 400
        assert RumVital.objects.count() == 0

    def test_value_out_of_bounds_rejected(self, anon_client):
        for bad in (-1, 999_999):
            resp = anon_client.post(INGEST_URL, {"vitals": [_vital(value=bad)]}, format="json")
            assert resp.status_code == 400
        assert RumVital.objects.count() == 0

    def test_oversized_batch_rejected(self, anon_client):
        resp = anon_client.post(INGEST_URL, {"vitals": [_vital()] * 11}, format="json")
        assert resp.status_code == 400
        assert RumVital.objects.count() == 0

    def test_empty_batch_rejected(self, anon_client):
        resp = anon_client.post(INGEST_URL, {"vitals": []}, format="json")
        assert resp.status_code == 400

    def test_anon_burst_throttled(self, anon_client, monkeypatch):
        # DRF binds THROTTLE_RATES as a CLASS attribute at import — mutating
        # settings.REST_FRAMEWORK does nothing here. Pin the rate on the
        # class itself, exactly as settings/test.py's comment prescribes.
        from apps.core.throttling import RumIngestAnonThrottle

        monkeypatch.setattr(RumIngestAnonThrottle, "THROTTLE_RATES", {"rum_ingest": "3/min"})
        cache.clear()
        try:
            statuses = [
                anon_client.post(INGEST_URL, {"vitals": [_vital()]}, format="json").status_code
                for _ in range(4)
            ]
            assert statuses[:3] == [204, 204, 204]
            assert statuses[3] == 429
        finally:
            cache.clear()


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_p75_nearest_rank():
    # 75% of 4 samples → the 3rd ordered value, not an interpolation.
    assert _p75([2000.0, 1000.0, 1000.0, 1000.0]) == 1000.0
    assert _p75([1.0, 2.0, 3.0, 4.0]) == 3.0
    assert _p75([42.0]) == 42.0


@pytest.mark.django_db
class TestRumSummary:
    def test_student_forbidden(self, student_client):
        assert student_client.get(SUMMARY_URL).status_code == 403

    def test_anonymous_rejected(self, anon_client):
        assert anon_client.get(SUMMARY_URL).status_code in (401, 403)

    def test_p75_and_segments(self, admin_client):
        for value, device in [
            (1000, "mobile"),
            (1000, "mobile"),
            (1000, "desktop"),
            (2000, "mobile"),
        ]:
            RumVital.objects.create(
                metric="LCP",
                value=value,
                rating="good",
                page_type="metier_fiche",
                device=device,
                connection="4g",
            )
        resp = admin_client.get(SUMMARY_URL)
        assert resp.status_code == 200
        [entry] = resp.json()["summary"]
        assert entry["metric"] == "LCP"
        assert entry["count"] == 4
        assert entry["p75"] == 1000.0
        # Nearest-rank p75 of 3 samples is the 3rd ordered value — for
        # [1000, 1000, 2000] that is 2000, not an interpolation. The first
        # version of this test expected 1000; the CODE was right.
        assert entry["by_device"]["mobile"] == {"count": 3, "p75": 2000.0}
        assert entry["by_device"]["desktop"] == {"count": 1, "p75": 1000.0}
        assert entry["by_connection"]["4g"]["count"] == 4

    def test_window_excludes_old_rows(self, admin_client):
        RumVital.objects.create(
            metric="LCP",
            value=1500,
            rating="good",
            page_type="home",
            device="mobile",
            connection="4g",
        )
        # `auto_now_add` ignores constructor args — backdate via update().
        RumVital.objects.update(created_at=timezone.now() - timedelta(days=40))
        resp = admin_client.get(SUMMARY_URL + "?days=28")
        assert resp.json()["summary"] == []
        resp = admin_client.get(SUMMARY_URL + "?days=90")
        assert len(resp.json()["summary"]) == 1


@pytest.mark.django_db
def test_prune_command(admin_client):
    RumVital.objects.create(
        metric="TTFB",
        value=100,
        rating="good",
        page_type="home",
        device="desktop",
        connection="4g",
    )
    RumVital.objects.update(created_at=timezone.now() - timedelta(days=120))
    call_command("prune_rum_vitals", "--days", "90")
    assert RumVital.objects.count() == 0
