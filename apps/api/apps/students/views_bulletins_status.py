"""Endpoints for Story 2.5 — mode dégradé invisible (bulletins postpone + banner dismiss)."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BulletinsStatus, StudentProfile

_BANNER_DISMISS_DAYS = 7
_NO_POSTPONE_STATUSES = {BulletinsStatus.COMPLETED, BulletinsStatus.PARTIAL}


def _get_or_create_profile(user) -> StudentProfile:
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    return profile


class BulletinsPostponeView(APIView):
    """POST /api/v1/students/me/bulletins/postpone

    Marks the student's bulletins as postponed (AC1, AC2).
    Idempotent if already postponed.
    Returns 409 if bulletins are partial or completed.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        profile = _get_or_create_profile(request.user)

        if profile.bulletins_status in _NO_POSTPONE_STATUSES:
            return Response(
                {"detail": "Cannot postpone when bulletins are already submitted."},
                status=status.HTTP_409_CONFLICT,
            )

        if profile.bulletins_status != BulletinsStatus.POSTPONED:
            profile.bulletins_status = BulletinsStatus.POSTPONED
            profile.bulletins_postponed_at = timezone.now()
            profile.save(
                update_fields=["bulletins_status", "bulletins_postponed_at", "updated_at"]
            )

        return Response(
            {
                "bulletins_status": profile.bulletins_status,
                "bulletins_postponed_at": profile.bulletins_postponed_at,
            }
        )


class BulletinsBannerDismissView(APIView):
    """POST /api/v1/students/me/bulletins/banner/dismiss

    Sets a 7-day TTL on the postponed banner (AC3).
    Idempotent — refreshes the TTL on each call.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        profile = _get_or_create_profile(request.user)
        profile.bulletins_postponed_banner_dismissed_until = timezone.now() + timedelta(
            days=_BANNER_DISMISS_DAYS
        )
        profile.save(
            update_fields=[
                "bulletins_postponed_banner_dismissed_until",
                "updated_at",
            ]
        )
        return Response(
            {
                "bulletins_postponed_banner_dismissed_until": (
                    profile.bulletins_postponed_banner_dismissed_until
                )
            }
        )
