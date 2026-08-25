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
    """A Bulletin + its BulletinOCRJob (created by the upload endpoint in
    production, per `ocr_extract`'s docstring — the task looks the job up by
    `bulletin_id` and errors "job not found" if none exists, so the fixture
    must create both rows for `ocr_extract()` to be callable directly)."""
    bulletin = Bulletin.objects.create(
        student=student,
        file_path="bulletins/test/bulletin.pdf",
        original_filename="bulletin.pdf",
        file_size_bytes=50_000,
        mime_type="application/pdf",
        uploaded_status=UploadedStatus.UPLOADED,
    )
    BulletinOCRJob.objects.create(bulletin=bulletin)
    return bulletin


def _make_clean_result():
    # Key convention matches the real `TesseractProvider` (tesseract.py):
    # every subject repeats the SAME key ("matiere" / "note"), never an
    # indexed variant ("matiere_0") — `BulletinOCRJob.is_low_quality`
    # counts `key == "matiere"` entries, so an indexed key would always
    # under-count and (incorrectly) flag every clean result as low quality.
    return OCRExtractionResult(
        fields=[
            OCRField(key="trimestre", value="T1", confidence=0.95, bbox=None),
            OCRField(key="annee", value="2024-2025", confidence=0.92, bbox=None),
            OCRField(key="matiere", value="Mathématiques", confidence=0.90, bbox=None),
            OCRField(key="note", value="15.5", confidence=0.88, bbox=None),
            OCRField(key="matiere", value="Français", confidence=0.91, bbox=None),
            OCRField(key="note", value="13", confidence=0.87, bbox=None),
            OCRField(key="matiere", value="Histoire-Géo", confidence=0.89, bbox=None),
            OCRField(key="note", value="14", confidence=0.86, bbox=None),
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
            OCRField(key="matiere", value="Maths", confidence=0.55, bbox=None),
            OCRField(key="note", value="12", confidence=0.50, bbox=None),
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
    @patch("apps.bulletins.tasks_ocr._provider")
    def test_clean_fixture_succeeds(self, mock_provider, mock_boto, bulletin):
        # `_provider` is a module-level singleton instantiated at import
        # time (`_provider = TesseractProvider()`), so patching the
        # `TesseractProvider` class has no effect on it — patch the
        # singleton instance directly.
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF")}
        mock_boto.return_value = mock_s3

        mock_provider.extract.return_value = _make_clean_result()

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.SUCCEEDED
        assert job.confidence_avg >= 0.7
        assert job.is_low_quality is False

    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr._provider")
    def test_partial_fixture_low_quality(self, mock_provider, mock_boto, bulletin):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF")}
        mock_boto.return_value = mock_s3

        mock_provider.extract.return_value = _make_partial_result()

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.SUCCEEDED
        assert job.is_low_quality is True

    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr._provider")
    def test_failed_fixture_marks_failed(self, mock_provider, mock_boto, bulletin):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF")}
        mock_boto.return_value = mock_s3

        mock_provider.extract.side_effect = RuntimeError("Tesseract crash")

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.FAILED
        assert "Tesseract crash" in (job.error_message or "")

    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr._provider")
    def test_idempotent_on_terminal_state(self, mock_provider, mock_boto, bulletin):
        """Job already in SUCCEEDED → task must be a no-op."""
        # The `bulletin` fixture already creates the (OneToOne) job row —
        # move it straight to the terminal state instead of creating a
        # second one.
        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        job.status = OCRJobStatus.SUCCEEDED
        job.confidence_avg = 0.9
        job.save(update_fields=["status", "confidence_avg"])

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        # Provider must NOT have been called
        mock_provider.extract.assert_not_called()


@pytest.mark.django_db
class TestHEICConversion:
    @patch("apps.bulletins.tasks_ocr.boto3.client")
    @patch("apps.bulletins.tasks_ocr._provider")
    @patch("pillow_heif.register_heif_opener")
    def test_heic_triggers_conversion(self, mock_heif, mock_provider, mock_boto, student):
        # Code-review fix (2026-08): this test previously patched the
        # `TesseractProvider` CLASS, which has no effect on `tasks_ocr._provider`
        # (a singleton instantiated once at module-import time — same
        # class-vs-instance pitfall already fixed on the other tests in this
        # file). The mocked `extract` return value was silently never used;
        # the REAL Tesseract provider ran against fake `b"HEIC_DATA"` bytes
        # instead, and the test only asserted `register_heif_opener` was
        # called — it passed for the wrong reason and never actually
        # exercised the HEIC-success path it claims to test.
        #
        # `register_heif_opener` is imported locally inside the conversion
        # helper (`from pillow_heif import register_heif_opener`), so it is
        # never a `apps.bulletins.tasks_ocr` module attribute — patching it
        # there raised `AttributeError`. Patch it at its source instead.
        bulletin = Bulletin.objects.create(
            student=student,
            file_path="bulletins/test/photo.heic",
            original_filename="photo.heic",
            file_size_bytes=1_000_000,
            mime_type="image/heic",
            uploaded_status=UploadedStatus.UPLOADED,
        )
        BulletinOCRJob.objects.create(bulletin=bulletin)

        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"HEIC_DATA")}
        mock_boto.return_value = mock_s3

        mock_provider.extract.return_value = _make_clean_result()

        from apps.bulletins.tasks_ocr import ocr_extract

        ocr_extract(bulletin.id)

        # register_heif_opener should have been called for HEIC mime type
        mock_heif.assert_called_once()
        # The mocked provider's success result must have actually been used —
        # this is what the previous version of this test never verified.
        mock_provider.extract.assert_called_once()
        job = BulletinOCRJob.objects.get(bulletin=bulletin)
        assert job.status == OCRJobStatus.SUCCEEDED
