"""Celery task tests — archival, chain integrity, async CSV export."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.audit.models import AuditResult
from apps.audit.tasks import archive_old_logs, export_csv_to_s3, verify_chain_integrity
from apps.audit.tests.factories import AuditLogFactory


@pytest.mark.django_db
def test_archive_old_logs_uploads_to_s3_with_manifest(settings):
    settings.AUDIT_ARCHIVE_AFTER_DAYS = 1
    old_created_at = timezone.now() - timedelta(days=10)
    AuditLogFactory.create(action="archive.candidate", created_at=old_created_at)

    fake_client = MagicMock()
    with patch("apps.audit.services.archive_service._s3_client", return_value=fake_client):
        result = archive_old_logs()

    assert result["archived"] == 1
    # Two put_object calls: archive.jsonl.gz + manifest.json.
    assert fake_client.put_object.call_count == 2
    call_args = [c.kwargs for c in fake_client.put_object.call_args_list]
    keys = [c["Key"] for c in call_args]
    assert any(k.endswith(".jsonl.gz") for k in keys)
    assert any(k.endswith("manifest.json") for k in keys)


@pytest.mark.django_db
def test_archive_old_logs_skipped_when_no_eligible_rows(settings):
    settings.AUDIT_ARCHIVE_AFTER_DAYS = 365
    # No rows old enough.
    AuditLogFactory.create(created_at=timezone.now())

    with patch("apps.audit.services.archive_service._s3_client") as s3:
        result = archive_old_logs()

    assert result == {"archived": 0}
    assert not s3.called


@pytest.mark.django_db
def test_verify_chain_integrity_returns_empty_broken_rows_for_intact_chain():
    """A chain produced by the decorator path should pass integrity verification."""
    from apps.audit.decorators import record_audit

    record_audit(action="chain.first", result=AuditResult.SUCCESS)
    record_audit(action="chain.second", result=AuditResult.SUCCESS)
    record_audit(action="chain.third", result=AuditResult.SUCCESS)

    result = verify_chain_integrity(window_days=1)

    # Note: the integrity task itself records `audit.integrity_check_completed` at the END,
    # which extends the chain. That row is verified next time. For the current run,
    # broken_rows must remain empty.
    assert result["broken_rows"] == []
    assert result["verified_rows"] >= 3


@pytest.mark.django_db
def test_verify_chain_integrity_detects_tampered_row():
    """Force a hash mismatch via direct ORM update (bypass the manager) and expect detection."""
    from apps.audit.decorators import record_audit

    record_audit(action="tamper.first", result=AuditResult.SUCCESS)
    second = record_audit(action="tamper.second", result=AuditResult.SUCCESS)
    assert second is not None

    # Tamper directly via the underlying queryset's _raw_delete-ish trick: we cannot use
    # .update() (blocked), so we mutate the in-memory row and bypass the save() guard by
    # calling super().save(update_fields=...) on the model class directly.
    second.metadata = {"tampered": True}
    from django.db.models import Model

    Model.save(second, update_fields=["metadata"])

    result = verify_chain_integrity(window_days=1)
    assert second.id in result["broken_rows"]


@pytest.mark.django_db
def test_export_csv_to_s3_uploads_with_csv_header():
    AuditLogFactory.create(action="async.export.row1")
    AuditLogFactory.create(action="async.export.row2")

    fake_client = MagicMock()
    with patch("apps.audit.tasks.boto3.client", return_value=fake_client):
        result = export_csv_to_s3(filters={"action": "async."}, requested_by="usr_admin")

    assert result["row_count"] == 2
    assert fake_client.put_object.called
    put_kwargs = fake_client.put_object.call_args.kwargs
    assert put_kwargs["ContentType"].startswith("text/csv")
    assert put_kwargs["Bucket"] == "exports-gdpr"  # Story 1.13 review P10
    assert put_kwargs["Key"].startswith("exports/usr_admin/")
    assert put_kwargs["ServerSideEncryption"] == "AES256"
    # Body carries the UTF-8 BOM so Excel renders accents correctly.
    body = put_kwargs["Body"].decode("utf-8")
    assert body.startswith("﻿")
    assert "async.export.row1" in body
    assert "async.export.row2" in body
    assert body.splitlines()[0].lstrip("﻿").startswith("id,created_at,actor_id")
    # Presigned URL is generated (Story 1.13 review P11).
    assert "url" in result
    assert fake_client.generate_presigned_url.called
