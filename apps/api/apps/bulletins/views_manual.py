"""Views for Story 2.4 — manual bulletin POST + PATCH."""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.students.models import StudentProfile

from .models import BulletinManual
from .serializers_manual import BulletinManualCreateSerializer, BulletinManualPatchSerializer


def _get_profile(user) -> StudentProfile:
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    return profile


class BulletinManualListView(APIView):
    """POST /api/v1/students/me/bulletins/manual — create a new manual bulletin."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        profile = _get_profile(request.user)
        serializer = BulletinManualCreateSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            # Empty matieres list → semantic validation failure → 422
            matieres_raw = request.data.get("matieres")
            if isinstance(matieres_raw, list) and len(matieres_raw) == 0:
                return Response(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        bulletin = serializer.save(student=profile)
        return Response(
            BulletinManualCreateSerializer(bulletin).data,
            status=status.HTTP_201_CREATED,
        )


class BulletinManualDetailView(APIView):
    """PATCH /api/v1/students/me/bulletins/manual/{pk}."""

    permission_classes = [IsAuthenticated]

    def _get_bulletin(self, pk: str, user) -> BulletinManual:
        profile = _get_profile(user)
        try:
            return BulletinManual.objects.get(pk=pk, student=profile)
        except BulletinManual.DoesNotExist:
            raise NotFound()

    def patch(self, request: Request, pk: str) -> Response:
        bulletin = self._get_bulletin(pk, request.user)
        serializer = BulletinManualPatchSerializer(bulletin, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)
