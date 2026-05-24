"""Story 1.11 — Celery tasks: build/notify/expire."""

from __future__ import annotations

import io
from datetime import timedelta
from unittest.mock import patch

import pytest
import pyzipper
from django.core import mail
from django.utils import timezone

from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.tasks import (
    build_export,
    expire_old_exports,
    notify_export_ready,
)
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_build_export_happy_path(fake_s3, settings):
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id)

    with patch("apps.accounts.tasks.notify_export_ready.delay"):
        result = build_export(export_id=export.id)

    export.refresh_from_db()
    assert export.status == GdprExportStatus.READY
    assert export.archive_s3_key == f"gdpr-exports/{user.id}/{export.id}.zip"
    assert export.archive_size_bytes is not None and export.archive_size_bytes > 0
    assert export.archive_sha256 is not None and len(export.archive_sha256) == 64
    assert export.password_hash is not None
    assert export.ready_at is not None
    assert export.expires_at is not None
    assert (export.expires_at - export.ready_at).days == settings.GDPR_EXPORT_VALIDITY_DAYS

    # S3 stub recorded the upload with AES256 SSE.
    key = (settings.GDPR_EXPORTS_BUCKET, export.archive_s3_key)
    stored = fake_s3.objects[key]
    assert stored["ServerSideEncryption"] == "AES256"
    assert stored["ContentType"] == "application/zip"
    assert result["sha256"] == export.archive_sha256


@pytest.mark.django_db
def test_build_export_is_idempotent_on_replay(fake_s3):
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id, status=GdprExportStatus.READY)
    result = build_export(export_id=export.id)
    assert result == {"skipped": "ready"}


@pytest.mark.django_db
def test_build_export_zip_opens_with_generated_password(fake_s3, settings):
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id)
    # Capture the password issued by the task by patching `secrets.token_urlsafe`.
    with (
        patch("apps.accounts.tasks.secrets.token_urlsafe", return_value="testpw-32chars-randomish"),
        patch("apps.accounts.tasks.notify_export_ready.delay"),
    ):
        build_export(export_id=export.id)

    export.refresh_from_db()
    stored = fake_s3.objects[(settings.GDPR_EXPORTS_BUCKET, export.archive_s3_key)]
    body = stored["Body"]

    # Decrypt and inspect the ZIP contents.
    with pyzipper.AESZipFile(io.BytesIO(body)) as zf:
        zf.setpassword(b"testpw-32chars-randomish")
        names = set(zf.namelist())
        assert "README.txt" in names
        assert "manifest.json" in names
        assert "profile/profile.json" in names
        # Read profile to confirm content matches the user.
        with zf.open("profile/profile.json") as f:
            payload = f.read().decode("utf-8")
            assert user.email in payload

    # Wrong password fails.
    with pyzipper.AESZipFile(io.BytesIO(body)) as zf:
        zf.setpassword(b"wrong-password")
        with pytest.raises(RuntimeError):
            zf.read("README.txt")


@pytest.mark.django_db
def test_build_export_marks_failed_when_s3_raises(fake_s3, settings):
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id)

    def _explode(**_kwargs):
        raise RuntimeError("S3 down — boto internal detail user must not see")

    with patch.object(fake_s3, "put_object", side_effect=_explode):
        build_export(export_id=export.id)

    export.refresh_from_db()
    assert export.status == GdprExportStatus.FAILED
    assert export.error_code == "gdpr.build_failed"
    # Post-review patch: error_message must NOT leak raw exception details
    # (boto endpoint, region, paths). Only the class name + safe pointer to Sentry.
    assert export.error_message == "RuntimeError: see Sentry for details."
    assert "S3 down" not in (export.error_message or "")
    assert "boto" not in (export.error_message or "")


@pytest.mark.django_db
def test_build_export_purges_orphan_s3_on_post_upload_failure(fake_s3, settings):
    """Post-review patch: if put_object succeeds but a later step raises, the
    S3 object MUST be deleted before transitioning to failed. Without this,
    encrypted user data is orphaned indefinitely on S3 → Art. 5(1)(e) breach.
    """
    user = UserFactory()
    export = GdprExportRequest.objects.create(user_id=user.id)

    # Let put_object succeed, then force the subsequent `save()` to raise.
    real_save = GdprExportRequest.save
    save_calls = {"n": 0}

    def flaky_save(self, *args, **kwargs):
        save_calls["n"] += 1
        # First save (status=IN_PROGRESS) must succeed; second one (status=READY)
        # must raise so we exercise the orphan-cleanup path.
        if save_calls["n"] == 2:
            raise RuntimeError("DB hiccup right after put_object")
        return real_save(self, *args, **kwargs)

    with patch.object(GdprExportRequest, "save", flaky_save):
        build_export(export_id=export.id)

    export.refresh_from_db()
    assert export.status == GdprExportStatus.FAILED
    # The orphan that was uploaded must have been deleted.
    key = f"gdpr-exports/{user.id}/{export.id}.zip"
    assert (settings.GDPR_EXPORTS_BUCKET, key) not in fake_s3.objects
    assert (settings.GDPR_EXPORTS_BUCKET, key) in fake_s3.delete_calls


@pytest.mark.django_db
def test_notify_export_ready_records_audit_and_sentry_when_no_email(fake_s3):
    """Post-review patch: silent strand previously left exports `ready` with
    no notification and no trace. Now we audit + Sentry-flag the skip.
    """
    import sys
    from unittest.mock import MagicMock

    user = UserFactory(email="x@example.test")
    export = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
    )
    # Empty the user's email so the no_email branch fires.
    user.email = ""
    user.save(update_fields=["email"])

    # `import sentry_sdk` happens inside the task at call time — replace the
    # module in sys.modules so the local import resolves to our mock.
    sentry_mock = MagicMock()
    with patch.dict(sys.modules, {"sentry_sdk": sentry_mock}):
        result = notify_export_ready(export_id=export.id, password="ignored")

    assert result == {"skipped": "no_email"}
    from apps.audit.models import AuditLog

    assert AuditLog.objects.filter(
        action="gdpr.notify_skipped",
        subject_id=user.id,
        result="failure",
    ).exists()
    sentry_mock.capture_message.assert_called_once()


@pytest.mark.django_db
def test_notify_export_ready_sends_both_emails_in_single_task(fake_s3, settings):
    """Post-review D1 (2026-05-24): a single task sends BOTH emails in-process so
    the cleartext password never traverses the broker between two tasks.
    """
    user = UserFactory(email="sarah@example.test")
    export = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
    )

    # `time.sleep(30)` between the two sends is the in-process gap; patch it
    # out so the test runs instantly.
    with patch("apps.accounts.tasks.time.sleep") as mock_sleep:
        notify_export_ready(export_id=export.id, password="secretpw")

    mock_sleep.assert_called_once_with(30)

    # Both emails sent from the same task — no follow-up apply_async.
    assert len(mail.outbox) == 2
    link_email = mail.outbox[0]
    password_email = mail.outbox[1]
    assert "sarah@example.test" in link_email.to
    assert "sarah@example.test" in password_email.to
    # Password ONLY in the second email, never in the first.
    assert "secretpw" not in link_email.body
    assert "secretpw" in password_email.body
    # Deep-link variant of the URL must include the export id (#anchor).
    assert export.id in link_email.body

    # Idempotence: re-run does nothing thanks to the emails_sent_at guard set
    # BEFORE the first send.
    export.refresh_from_db()
    assert export.emails_sent_at is not None
    mail.outbox.clear()
    with patch("apps.accounts.tasks.time.sleep") as mock_sleep_2:
        result = notify_export_ready(export_id=export.id, password="secretpw")
    assert result == {"skipped": "already_sent"}
    assert mail.outbox == []
    mock_sleep_2.assert_not_called()


@pytest.mark.django_db
def test_expire_old_exports_purges_s3_and_transitions(fake_s3, settings):
    user = UserFactory()
    # 3 ready exports: 2 expired, 1 still valid.
    expired_a = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now() - timedelta(days=10),
        expires_at=timezone.now() - timedelta(days=3),
        archive_s3_key=f"gdpr-exports/{user.id}/a.zip",
    )
    expired_b = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now() - timedelta(days=9),
        expires_at=timezone.now() - timedelta(days=2),
        archive_s3_key=f"gdpr-exports/{user.id}/b.zip",
    )
    fresh = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
        archive_s3_key=f"gdpr-exports/{user.id}/c.zip",
    )

    fake_s3.objects[(settings.GDPR_EXPORTS_BUCKET, expired_a.archive_s3_key)] = {"Body": b""}
    fake_s3.objects[(settings.GDPR_EXPORTS_BUCKET, expired_b.archive_s3_key)] = {"Body": b""}
    fake_s3.objects[(settings.GDPR_EXPORTS_BUCKET, fresh.archive_s3_key)] = {"Body": b""}

    result = expire_old_exports()
    assert result["expired"] == 2

    expired_a.refresh_from_db()
    expired_b.refresh_from_db()
    fresh.refresh_from_db()
    assert expired_a.status == GdprExportStatus.EXPIRED
    assert expired_a.archive_s3_key is None
    assert expired_b.status == GdprExportStatus.EXPIRED
    assert fresh.status == GdprExportStatus.READY
    assert (settings.GDPR_EXPORTS_BUCKET, f"gdpr-exports/{user.id}/c.zip") in fake_s3.objects


@pytest.mark.django_db
def test_expire_old_exports_keeps_ready_when_s3_delete_fails(fake_s3, settings):
    user = UserFactory()
    expired = GdprExportRequest.objects.create(
        user_id=user.id,
        status=GdprExportStatus.READY,
        ready_at=timezone.now() - timedelta(days=10),
        expires_at=timezone.now() - timedelta(days=3),
        archive_s3_key=f"gdpr-exports/{user.id}/x.zip",
    )
    fake_s3.fail_on_delete = True

    result = expire_old_exports()
    assert result["expired"] == 0

    expired.refresh_from_db()
    # Still ready — we'll retry next nightly run rather than lose the S3 ref.
    assert expired.status == GdprExportStatus.READY
