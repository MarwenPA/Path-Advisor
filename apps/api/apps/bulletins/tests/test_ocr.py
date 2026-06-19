"""OCR job tests — Story 2.3 T5 (backend)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from apps.bulletins.models import Bulletin, BulletinOCRJob, OCRJobStatus, UploadedStatus
from apps.bulletins.providers.base import OCRExtractionResult, OCRField

User = get_user_model()


@pytest.fixture
def student(db):
    from django.utils import timezone

    return User.objects.create_user(
        email="student@ocr.local",
        password="Strong1!pass",
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def bulletin(student):
    return Bulletin.objects.create(
        student=student,
        file_path="bulletins/test/bulletin.pdf",
        original_filename="bulletin.pdf",
        file_size_bytes=50_000,
        mime_type="application/pdf",
        uploaded_status=UploadedStatus.UPLOADED,
    )


def _make_clean_result():
    return OCRExtractionResult(
        fields=[
            OCRField(key="trimestre", value="T1", confidence=0.95, bbox=None),
            OCRField(key="annee", value="2024-2025", confidence=0.92, bbox=None),
            OCRField(key="matiere_0", value="Mathématiques", confidence=0.90, bbox=None),
            OCRField(key="note_0", value="15.5", confidence=0.88, bbox=None),
            OCRField(key="matiere_1", value="Français", confidence=0.91, bbox=None),
            OCRField(key="note_1", value="13", confidence=0.87, bbox=None),
            OCRField(key="matiere_2", value="Histoire-Géo", confidence=0.89, bbox=None),
            OCRField(key="note_2", value="14", confidence=0.86, bbox=None),
        ],
        raw_text="Bulletin T1 2024-2025\nMathématiques 15.5\nFrançais 13\nHistoire-Géo 14",
        language="fra",
        processing_ms=800,
        provider="tesseract",
        provider_version="5.3.0",
    )


def _make_partial_result():
    """< 3 matières — low quality."""
    return OCRExtractionResult(
        fields=[
            OCRField(key="trimestre", value="T2", confidence=0.80, bbox=None),
            OCRField(key="matiere_0", value="Maths", confidence=0.55, bbox=None),
            OCRField(key="note_0", value="12", confidence=0.50, bbox=None),
        ],
        raw_text="Partial extraction",
        language="fra",
        processing_ms=300,
        provider="tesseract",
        provider_version="5.3.0",
    )


def _make_failed_result():
    return OCRExtractionResult(
        fields=[],
        raw_text="",
        language="fra",
        processing_ms=100,
        provider="tesseract",
        provider_version="5.3.0",
    )


@pytest.mark.django_db
class TestOCRTaskClean:
    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr.TesseractProvider")
    def test_clean_fixture_succeeds(self, MockProvider, mock_boto, bulletin):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF")}
        mock_boto.return_value = mock_s3

        provider_instance = MagicMock()
        provider_instance.extract.return_value = _make_clean_result()
        MockProvider.return_value = provider_instance

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.SUCCEEDED
        assert job.confidence_avg >= 0.7
        assert job.is_low_quality is False

    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr.TesseractProvider")
    def test_partial_fixture_low_quality(self, MockProvider, mock_boto, bulletin):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF")}
        mock_boto.return_value = mock_s3

        provider_instance = MagicMock()
        provider_instance.extract.return_value = _make_partial_result()
        MockProvider.return_value = provider_instance

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.SUCCEEDED
        assert job.is_low_quality is True

    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr.TesseractProvider")
    def test_failed_fixture_marks_failed(self, MockProvider, mock_boto, bulletin):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF")}
        mock_boto.return_value = mock_s3

        provider_instance = MagicMock()
        provider_instance.extract.side_effect = RuntimeError("Tesseract crash")
        MockProvider.return_value = provider_instance

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.FAILED
        assert "Tesseract crash" in (job.error_message or "")

    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr.TesseractProvider")
    def test_idempotent_on_terminal_state(self, MockProvider, mock_boto, bulletin):
        """Job already in SUCCEEDED → task must be a no-op."""
        BulletinOCRJob.objects.create(
            bulletin=bulletin,
            status=OCRJobStatus.SUCCEEDED,
            confidence_avg=0.9,
        )
        provider_instance = MagicMock()
        MockProvider.return_value = provider_instance

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        # Provider must NOT have been called
        provider_instance.extract.assert_not_called()


@pytest.mark.django_db
class TestHEICConversion:
    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr.TesseractProvider")
    @patch("apps.bulletins.tasks_ocr.register_heif_opener")
    def test_heic_triggers_conversion(self, mock_heif, MockProvider, mock_boto, student):
        bulletin = Bulletin.objects.create(
            student=student,
            file_path="bulletins/test/photo.heic",
            original_filename="photo.heic",
            file_size_bytes=1_000_000,
            mime_type="image/heic",
            uploaded_status=UploadedStatus.UPLOADED,
        )

        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"HEIC_DATA")}
        mock_boto.return_value = mock_s3

        provider_instance = MagicMock()
        provider_instance.extract.return_value = _make_clean_result()
        MockProvider.return_value = provider_instance

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        # register_heif_opener should have been called for HEIC mime type
        mock_heif.assert_called_once()
