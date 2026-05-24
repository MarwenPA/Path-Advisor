"""Story 1.11 — GdprExportRequest model invariants."""

from __future__ import annotations

import pytest

from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_gdpr_export_id_uses_gex_prefix():
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id)
    assert export.id.startswith("gex_")
    assert len(export.id) > 4


@pytest.mark.django_db
def test_gdpr_export_defaults_pending():
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id)
    assert export.status == GdprExportStatus.PENDING
    assert export.requested_at is not None
    assert export.ready_at is None
    assert export.expires_at is None
    assert export.download_count == 0
    assert export.emails_sent_at is None
    assert export.archive_s3_key is None
    assert export.password_hash is None


@pytest.mark.django_db
def test_gdpr_export_status_choices_are_lowercase_snake():
    for value, _ in GdprExportStatus.choices:
        assert value.islower()
        assert " " not in value


@pytest.mark.django_db
def test_is_active_and_is_downloadable_properties():
    user = UserFactory()
    pending = GdprExportRequest.objects.create(user_id=user.id)
    assert pending.is_active is True
    assert pending.is_downloadable is False

    pending.status = GdprExportStatus.READY
    assert pending.is_active is False
    assert pending.is_downloadable is True

    pending.status = GdprExportStatus.EXPIRED
    assert pending.is_active is False
    assert pending.is_downloadable is False


@pytest.mark.django_db
def test_db_table_is_pluralised_snake_case():
    assert GdprExportRequest._meta.db_table == "gdpr_export_requests"
