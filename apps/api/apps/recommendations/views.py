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
            if "unique_student_profession_review" in str(exc):
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
