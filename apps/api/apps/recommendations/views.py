"""Story 3.4 — GET /api/v1/students/me/recommendations/.
Story 3.7 — POST /api/v1/students/me/recommendation-reviews/ (RGPD art. 22).
"""

from __future__ import annotations

from typing import ClassVar

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsAuthenticatedAndActive, IsPathAdmin, IsStudent
from apps.professions.models import Profession

from .models import RecommendationReview
from .serializers import (
    RecommendationReviewAdminSerializer,
    RecommendationReviewCreateSerializer,
    RecommendationReviewResponseSerializer,
)
from .services import ai_client
from .services.recommendation_service import compute_recommendations


class RecommendationsView(APIView):
    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request) -> Response:
        try:
            data = compute_recommendations(request.user)
        except ai_client.AIServiceUnavailableError as exc:
            return Response(
                {"title": "Service IA indisponible", "detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "results": data["results"],
                "niveau_adapted": data["niveau_adapted"],
                "computed_at": timezone.now().isoformat(),
                # Story 9.5 — art. 22: every scoring answer carries the model
                # version that produced it + its journal entry id.
                "model_version": data.get("model_version", ""),
                "decision_id": data.get("decision_id"),
            }
        )


class _ReviewPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class RecommendationReviewCreateView(APIView):
    """POST /api/v1/students/me/recommendation-reviews/

    RGPD art. 22 — student requests human review of a vocational recommendation.
    One request per (student, profession); returns 409 if already submitted.
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request: Request) -> Response:
        serializer = RecommendationReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        slug = serializer.validated_data["profession_slug"]
        try:
            # Lookup by slug only — no is_active filter, so students can always contest
            # a recommendation they received even if the profession was later deactivated.
            profession = Profession.objects.get(slug=slug)
        except Profession.DoesNotExist:
            return Response({"detail": "Profession introuvable."}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                review = RecommendationReview.objects.create(
                    student=request.user,
                    profession=profession,
                    reason=serializer.validated_data["reason"],
                    comment=serializer.validated_data.get("comment") or None,
                )
                record_audit(
                    action="recommendation_review_requested",
                    result=AuditResult.SUCCESS,
                    actor=request.user,
                    subject_id=review.id,
                    metadata={
                        "profession_slug": slug,
                        "reason": review.reason,
                        "student_id": str(request.user.pk),
                        "review_id": review.id,
                    },
                )
        except IntegrityError as exc:
            # Message text differs by backend: PostgreSQL names the violated
            # constraint ("unique_student_profession_review"); SQLite (used
            # by the fast test lane) reports the column pair instead
            # ("UNIQUE constraint failed: ...student_id, ...profession_id").
            # Match either so the 409 branch is portable across both.
            msg = str(exc)
            is_duplicate_review = "unique_student_profession_review" in msg or (
                "UNIQUE constraint failed" in msg and "student_id" in msg and "profession_id" in msg
            )
            if is_duplicate_review:
                return Response(
                    {"detail": "Une demande de revue existe déjà pour ce métier."},
                    status=status.HTTP_409_CONFLICT,
                )
            raise

        # TODO(story-8-1): send confirmation email to student
        return Response(
            RecommendationReviewResponseSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class RecommendationReviewAdminListView(APIView):
    """GET /api/v1/admin/recommendation-reviews/

    Returns paginated pending review requests for admin processing (Epic 9).
    """

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request) -> Response:
        qs = (
            RecommendationReview.objects.filter(status=RecommendationReview.Status.PENDING)
            .select_related("student", "profession")
            .order_by("-created_at")
        )
        paginator = _ReviewPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = RecommendationReviewAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminModelVersionsView(APIView):
    """GET/POST /api/v1/admin/model-versions/ — Story 9.5 governance list +
    registration (dataset hash computed at registration time)."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request) -> Response:
        from .models import ModelVersion

        rows = ModelVersion.objects.select_related("deployed_by").all()
        return Response(
            {
                "versions": [
                    {
                        "id": row.pk,
                        "name": row.name,
                        "version": row.version,
                        "dataset_hash": row.dataset_hash,
                        "hyperparameters": row.hyperparameters_json,
                        "evaluation_metrics": row.evaluation_metrics_json,
                        "max_subpopulation_gap": round(row.max_subpopulation_gap(), 4),
                        "is_active": row.is_active,
                        "requires_ethics_review": row.requires_ethics_review,
                        "ethics_review_note": row.ethics_review_note,
                        "deployed_at": row.deployed_at.isoformat() if row.deployed_at else None,
                        "deployed_by": row.deployed_by.email if row.deployed_by else None,
                        "decisions_count": row.decisions.count(),
                        "created_at": row.created_at.isoformat(),
                    }
                    for row in rows
                ]
            }
        )

    def post(self, request: Request) -> Response:
        from .model_governance import register_model_version

        name = (request.data.get("name") or "").strip()
        version = (request.data.get("version") or "").strip()
        hyperparameters = request.data.get("hyperparameters") or {}
        if not name or not version or not isinstance(hyperparameters, dict):
            return Response(
                {"detail": "name, version et hyperparameters (objet) sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        row = register_model_version(
            editor=request.user,
            name=name,
            version=version,
            hyperparameters=hyperparameters,
            evaluation_metrics=request.data.get("evaluation_metrics") or {},
        )
        return Response({"id": row.pk, "dataset_hash": row.dataset_hash}, status=201)


class AdminModelVersionActivateView(APIView):
    """POST /api/v1/admin/model-versions/{id}/activate/ — ethics-gated."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsPathAdmin]

    def post(self, request: Request, version_id: str) -> Response:
        from .model_governance import EthicsGateError, activate_model_version
        from .models import ModelVersion

        row = ModelVersion.objects.filter(pk=version_id).first()
        if row is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            row = activate_model_version(
                version_row=row,
                editor=request.user,
                ethics_note=(request.data.get("ethics_note") or ""),
            )
        except EthicsGateError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"id": row.pk, "is_active": row.is_active})
