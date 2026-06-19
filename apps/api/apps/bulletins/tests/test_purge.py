"""Purge job tests — Story 2.3 T5 (backend)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.bulletins.models import Bulletin, UploadedStatus

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="purge@test.local",
        password="Strong1!pass",
        email_verified_at=timezone.now(),
    )


@pytest.mark.django_db
class TestPurge:
    @patch("apps.bulletins.tasks_purge.boto3.client")
    def test_expired_unvalidated_bulletin_is_deleted(self, mock_boto, student):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        expired = Bulletin.objects.create(
            student=student,
            file_path="bulletins/student/expired.pdf",
            original_filename="expired.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
            uploaded_status=UploadedStatus.UPLOADED,
            expires_at=timezone.now() - timedelta(days=1),
        )

        from apps.bulletins.tasks_purge import purge_expired_bulletins

        purge_expired_bulletins()

        assert not Bulletin.objects.filter(pk=expired.pk).exists()
        mock_s3.delete_object.assert_called_once()

    @patch("apps.bulletins.tasks_purge.boto3.client")
    def test_validated_bulletin_is_kept(self, mock_boto, student):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        validated = Bulletin.objects.create(
            student=student,
            file_path="bulletins/student/validated.pdf",
            original_filename="validated.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
            uploaded_status=UploadedStatus.UPLOADED,
            expires_at=timezone.now() - timedelta(days=1),
            validated_at=timezone.now() - timedelta(days=5),
        )

        from apps.bulletins.tasks_purge import purge_expired_bulletins

        purge_expired_bulletins()

        assert Bulletin.objects.filter(pk=validated.pk).exists()
        mock_s3.delete_object.assert_not_called()

    @patch("apps.bulletins.tasks_purge.boto3.client")
    def test_future_expiry_bulletin_is_kept(self, mock_boto, student):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        future = Bulletin.objects.create(
            student=student,
            file_path="bulletins/student/future.pdf",
            original_filename="future.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
            uploaded_status=UploadedStatus.UPLOADED,
            expires_at=timezone.now() + timedelta(days=10),
        )

        from apps.bulletins.tasks_purge import purge_expired_bulletins

        purge_expired_bulletins()

        assert Bulletin.objects.filter(pk=future.pk).exists()
