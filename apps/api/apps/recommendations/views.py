"""Story 3.4 — GET /api/v1/students/me/recommendations/."""

from __future__ import annotations

from typing import ClassVar

from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAuthenticatedAndActive, IsStudent

from .services import ai_client
from .services.recommendation_service import compute_recommendations


class RecommendationsView(APIView):
    permission_classes: ClassVar = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request) -> Response:
        try:
            results = compute_recommendations(request.user)
        except ai_client.AIServiceUnavailableError as exc:
            return Response(
                {"title": "Service IA indisponible", "detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "results": results,
                "computed_at": timezone.now().isoformat(),
            }
        )
