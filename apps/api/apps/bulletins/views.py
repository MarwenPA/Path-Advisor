"""Bulletin upload, OCR start/status, and finalize endpoints — Story 2.3 T2/T3.

Routes (mounted under /api/v1/students/):
  POST   me/bulletins/upload              — AC2/AC3: upload one file
  POST   me/bulletins/ocr/start           — AC4: start OCR job(s)
  GET    me/bulletins/ocr/status          — AC4: poll OCR job status
  PATCH  me/bulletins/{bulletin_id}/finalize — AC5: commit corrected fields
"""

from __future__ import annotations

import logging
import uuid

import boto3
from botocore.config import Config
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.bulletins.models import Bulletin, BulletinOCRJob, OCRJobStatus, UploadedStatus
from apps.bulletins.serializers import (
    BulletinFinalizeSerializer,
    BulletinSerializer,
    BulletinUploadSerializer,
    OCRStartSerializer,
)
from apps.bulletins.tasks_ocr import ocr_extract
from apps.core.permissions import IsAuthenticatedAndActive, IsStudent

log = logging.getLogger(__name__)

_ESTIMATED_SECONDS_PER_BULLETIN = 8
_ESTIMATED_OVERHEAD_SECONDS = 5


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


class BulletinUploadView(APIView):
    """POST /api/v1/students/me/bulletins/upload — AC2/AC3."""

    permission_classes = (IsAuthenticatedAndActive, IsStudent)
    parser_classes = (MultiPartParser,)

    def post(self, request: Request) -> Response:
        ser = BulletinUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        file_obj = ser.validated_data["file"]

        # Guard: max 6 bulletins per student (AC2)
        existing_count = Bulletin.objects.filter(student=request.user).count()
        if existing_count >= 6:
            return Response(
                {"detail": "Maximum 6 fichiers — supprime-en pour en ajouter d'autres."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Build S3 key: bulletins/{student_id}/{uuid}/{filename}
        s3_key = (
            f"bulletins/{request.user.pk}/{uuid.uuid4().hex}/{file_obj.name}"
        )
        bucket = settings.BULLETINS_BUCKET

        try:
            s3 = _s3_client()
            s3.upload_fileobj(
                file_obj,
                bucket,
                s3_key,
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )
        except Exception as exc:
            log.error("S3 upload failed for user %s: %s", request.user.pk, exc)
            return Response(
                {"detail": "L'upload a échoué. Réessaie dans quelques secondes."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Snapshot student level for subjects_ref_version (AC8)
        level_at_upload = None
        subjects_ref_version = None
        try:
            level_profile = request.user.student_profile.level_profile
            level_at_upload = level_profile.level
            subjects_ref_version = level_profile.level_ref_version
        except Exception:
            pass

        bulletin = Bulletin.objects.create(
            student=request.user,
            file_path=s3_key,
            original_filename=file_obj.name,
            file_size_bytes=file_obj.size,
            mime_type=file_obj.content_type or "application/octet-stream",
            uploaded_status=UploadedStatus.UPLOADED,
            level_at_upload=level_at_upload,
            subjects_ref_version=subjects_ref_version,
        )

        record_audit(
            action="bulletin_uploaded",
            result=AuditResult.SUCCESS,
            subject_id=str(request.user.pk),
            metadata={"bulletin_id": bulletin.id, "mime_type": bulletin.mime_type},
        )

        return Response(BulletinSerializer(bulletin).data, status=status.HTTP_201_CREATED)


class OCRStartView(APIView):
    """POST /api/v1/students/me/bulletins/ocr/start — AC4."""

    permission_classes = (IsAuthenticatedAndActive, IsStudent)

    def post(self, request: Request) -> Response:
        ser = OCRStartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Deduplicate preserving order (#19)
        seen: set = set()
        bulletin_ids = [
            bid for bid in ser.validated_data["bulletin_ids"]
            if not (bid in seen or seen.add(bid))  # type: ignore[func-returns-value]
        ]

        # Ownership check — all bulletins must belong to request.user
        bulletins = Bulletin.objects.filter(
            id__in=bulletin_ids,
            student=request.user,
            uploaded_status=UploadedStatus.UPLOADED,
        )
        if bulletins.count() != len(bulletin_ids):
            return Response(
                {"detail": "Un ou plusieurs bulletins sont invalides ou n'appartiennent pas à ce compte."},
                status=status.HTTP_404_NOT_FOUND,
            )

        jobs = []
        for bulletin in bulletins:
            job, _ = BulletinOCRJob.objects.get_or_create(bulletin=bulletin)
            if job.status in (OCRJobStatus.FAILED, OCRJobStatus.TIMEOUT):
                # Allow retry on failed jobs
                job.status = OCRJobStatus.PENDING
                job.error_message = None
                job.save(update_fields=["status", "error_message"])
            jobs.append(job)

        # Dispatch Celery tasks (max 3 concurrent handled by worker pool config)
        for bulletin in bulletins:
            ocr_extract.delay(bulletin.id)

        estimated_seconds = (
            len(bulletin_ids) * _ESTIMATED_SECONDS_PER_BULLETIN + _ESTIMATED_OVERHEAD_SECONDS
        )

        return Response(
            {
                "job_ids": [j.id for j in jobs],
                "bulletin_ids": bulletin_ids,
                "estimated_seconds": estimated_seconds,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class OCRStatusView(APIView):
    """GET /api/v1/students/me/bulletins/ocr/status?bulletin_id=... — AC4."""

    permission_classes = (IsAuthenticatedAndActive, IsStudent)

    def get(self, request: Request) -> Response:
        bulletin_id = request.query_params.get("bulletin_id")
        if not bulletin_id:
            return Response(
                {"detail": "bulletin_id query param required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job = BulletinOCRJob.objects.select_related("bulletin").get(
                bulletin_id=bulletin_id,
                bulletin__student=request.user,
            )
        except BulletinOCRJob.DoesNotExist:
            return Response({"detail": "Job non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        payload: dict = {
            "job_id": job.id,
            "status": job.status,
            "extraction": None,
            "error": None,
        }

        if job.status == OCRJobStatus.SUCCEEDED:
            # Return normalized fields only (not raw extraction) for front-end recap
            payload["extraction"] = {
                "normalized_fields": job.normalized_fields,
                "confidence_avg": job.confidence_avg,
                "is_low_quality": job.is_low_quality,
            }
        elif job.status in (OCRJobStatus.FAILED, OCRJobStatus.TIMEOUT):
            payload["error"] = job.error_message or "OCR failed"

        return Response(payload)


class BulletinFinalizeView(APIView):
    """PATCH /api/v1/students/me/bulletins/{bulletin_id}/finalize — AC5."""

    permission_classes = (IsAuthenticatedAndActive, IsStudent)

    def patch(self, request: Request, bulletin_id: str) -> Response:
        try:
            bulletin = Bulletin.objects.get(id=bulletin_id, student=request.user)
        except Bulletin.DoesNotExist:
            return Response({"detail": "Bulletin non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        ser = BulletinFinalizeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Store corrected fields on the OCR job's normalized_fields
        # (original raw_extraction is never mutated — audit longitudinal)
        try:
            job = bulletin.ocr_job
            old_fields = job.normalized_fields or []
            corrected = ser.validated_data["fields"]
            job.normalized_fields = corrected
            job.save(update_fields=["normalized_fields", "updated_at"])

            record_audit(
                action="bulletin_finalized",
                result=AuditResult.SUCCESS,
                subject_id=str(request.user.pk),
                metadata={
                    "bulletin_id": bulletin_id,
                    "fields_corrected": len(corrected),
                    "previous_field_count": len(old_fields),
                },
            )
        except BulletinOCRJob.DoesNotExist:
            pass

        bulletin.mark_validated()
        bulletin.save(update_fields=["validated_at", "expires_at"])

        # Update student's bulletins_status on StudentProfile
        self._update_bulletins_status(request.user)

        return Response(BulletinSerializer(bulletin).data)

    @staticmethod
    def _update_bulletins_status(user) -> None:
        from apps.students.models import BulletinsStatus

        try:
            profile = user.student_profile
            validated_count = Bulletin.objects.filter(
                student=user,
                validated_at__isnull=False,
            ).count()

            if validated_count >= 2:
                profile.bulletins_status = BulletinsStatus.COMPLETED
            elif validated_count >= 1:
                profile.bulletins_status = BulletinsStatus.PARTIAL
            profile.save(update_fields=["bulletins_status", "updated_at"])
        except Exception:
            pass


class OnboardingStatusView(APIView):
    """GET /api/v1/students/me/bulletins/onboarding/status — DN1 resume logic.

    Returns the student's current onboarding bulletin state so the frontend
    machine can hydrate to the correct step on page reload (AC9).
    """

    permission_classes = (IsAuthenticatedAndActive, IsStudent)

    def get(self, request: Request) -> Response:
        bulletins = list(
            Bulletin.objects.filter(
                student=request.user,
                validated_at__isnull=True,
            )
            .prefetch_related("ocr_job")
            .order_by("created_at")
        )

        if not bulletins:
            return Response({"state": "idle"})

        bulletin_ids = [str(b.id) for b in bulletins]
        jobs: dict = {}
        for b in bulletins:
            try:
                jobs[str(b.id)] = b.ocr_job
            except BulletinOCRJob.DoesNotExist:
                jobs[str(b.id)] = None

        statuses = [j.status if j else None for j in jobs.values()]

        if any(s in (OCRJobStatus.PENDING, OCRJobStatus.RUNNING) for s in statuses):
            return Response({"state": "ocr_running", "bulletin_ids": bulletin_ids})

        if any(s in (OCRJobStatus.FAILED, OCRJobStatus.TIMEOUT) for s in statuses):
            return Response({"state": "fallback", "bulletin_ids": bulletin_ids})

        if all(s == OCRJobStatus.SUCCEEDED for s in statuses if s is not None):
            recaps = []
            for b in bulletins:
                job = jobs.get(str(b.id))
                if job and job.normalized_fields:
                    recaps.append({
                        "bulletinId": str(b.id),
                        "normalizedFields": job.normalized_fields,
                        "confidenceAvg": job.confidence_avg,
                        "isLowQuality": job.is_low_quality,
                    })
            if recaps:
                return Response({
                    "state": "recap_editing",
                    "bulletin_ids": bulletin_ids,
                    "recaps": recaps,
                })

        return Response({"state": "idle"})
