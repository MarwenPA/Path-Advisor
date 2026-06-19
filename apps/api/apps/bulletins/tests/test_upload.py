"""Upload endpoint tests — Story 2.3 T5 (backend)."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.bulletins.models import Bulletin, UploadedStatus

User = get_user_model()

URL = "/api/v1/students/me/bulletins/upload"


@pytest.fixture
def student_user(db):
    from django.utils import timezone

    return User.objects.create_user(
        email="student@test.local",
        password="Strong1!password",
        status=UserStatus.ACTIVE,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def auth_client(student_user):
    api = APIClient()
    api.force_authenticate(user=student_user)
    return api


def _make_file(name="bulletin.pdf", content=b"%PDF-1.4 test", content_type="application/pdf"):
    return io.BytesIO(content), name, content_type


@patch("apps.bulletins.views.boto3.client")
def _upload(auth_client, mock_boto, name="bulletin.pdf", content_type="application/pdf"):
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    buf = io.BytesIO(b"%PDF-1.4 test")
    buf.name = name
    response = auth_client.post(
        URL,
        {"file": buf},
        format="multipart",
        CONTENT_TYPE=content_type,
    )
    return response, mock_s3


@pytest.mark.django_db
class TestUploadFormats:
    def test_accepts_pdf(self, auth_client):
        with patch("apps.bulletins.views.boto3.client") as mock_boto:
            mock_boto.return_value = MagicMock()
            buf = io.BytesIO(b"%PDF-1.4")
            buf.name = "bulletin.pdf"
            response = auth_client.post(URL, {"file": buf}, format="multipart")
        assert response.status_code == 201

    def test_accepts_jpeg(self, auth_client):
        with patch("apps.bulletins.views.boto3.client") as mock_boto:
            mock_boto.return_value = MagicMock()
            buf = io.BytesIO(b"\xff\xd8\xff fake jpeg")
            buf.name = "bulletin.jpg"
            buf.content_type = "image/jpeg"
            response = auth_client.post(
                URL,
                {"file": ("bulletin.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")},
                format="multipart",
            )
        assert response.status_code == 201

    def test_rejects_unknown_format(self, auth_client):
        with patch("apps.bulletins.views.boto3.client") as mock_boto:
            mock_boto.return_value = MagicMock()
            buf = ("bulletin.exe", io.BytesIO(b"bad"), "application/x-msdownload")
            response = auth_client.post(URL, {"file": buf}, format="multipart")
        assert response.status_code == 400

    def test_rejects_oversized_file(self, auth_client):
        with patch("apps.bulletins.views.boto3.client") as mock_boto:
            mock_boto.return_value = MagicMock()
            big_content = b"x" * (11 * 1024 * 1024)  # 11 MB
            buf = ("big.pdf", io.BytesIO(big_content), "application/pdf")
            response = auth_client.post(URL, {"file": buf}, format="multipart")
        assert response.status_code == 400
        assert "10 MB" in response.json()["file"][0]

    def test_rejects_seventh_file(self, auth_client, student_user):
        # Create 6 existing bulletins
        for i in range(6):
            Bulletin.objects.create(
                student=student_user,
                file_path=f"bulletins/{student_user.pk}/test{i}.pdf",
                original_filename=f"bulletin{i}.pdf",
                file_size_bytes=1000,
                mime_type="application/pdf",
                uploaded_status=UploadedStatus.UPLOADED,
            )
        with patch("apps.bulletins.views.boto3.client") as mock_boto:
            mock_boto.return_value = MagicMock()
            buf = ("extra.pdf", io.BytesIO(b"%PDF"), "application/pdf")
            response = auth_client.post(URL, {"file": buf}, format="multipart")
        assert response.status_code == 422
        assert "Maximum 6" in response.json()["detail"]

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        buf = ("bulletin.pdf", io.BytesIO(b"%PDF"), "application/pdf")
        response = client.post(URL, {"file": buf}, format="multipart")
        assert response.status_code in (401, 403)
