"""Maturity endpoint — Story 2.7 AC2 + AC9.

GET /api/v1/students/me/profile/maturity
Returns { level, next_actions, computed_at }.

Auth: IsAuthenticatedAndActive + IsStudent (consistent with step-1 endpoints).
Computation is cheap + idempotent — no caching needed, computed on every GET.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAuthenticatedAndActive, IsStudent
from apps.students.models import StudentLevelProfile, StudentProfile
from apps.students.profile_maturity import MaturityLevel, compute_maturity


@dataclass
class _SnapAdapter:
    """Adapts Django model fields into the ProfileSnapshot protocol."""

    onboarding_step1_status: str
    passions_count: int
    onboarding_step2_status: str
    bulletins_status: str


def _next_actions_for(level: MaturityLevel) -> list[dict]:
    """Return next_actions per AC2 table — ordered by highest gain first."""
    if level == MaturityLevel.BASE:
        return [
            {
                "icon": "bulletins",
                "label": "Ajoute un bulletin",
                "benefit": "Tu débloques les stats personnalisées",
            },
            {
                "icon": "passions",
                "label": "Affine tes passions et valeurs",
                "benefit": "Tes recos métiers seront plus précises",
            },
        ]
    if level == MaturityLevel.ENRICHED:
        return [
            {
                "icon": "bulletins",
                "label": "Ajoute un autre trimestre",
                "benefit": "Tes stats deviennent encore plus précises",
            },
            {
                "icon": "specialites",
                "label": "Vérifie tes spécialités",
                "benefit": "Parcours encore mieux ciblés",
            },
        ]
    # complete
    return []


class ProfileMaturityView(APIView):
    """GET /api/v1/students/me/profile/maturity."""

    permission_classes = (IsAuthenticatedAndActive, IsStudent)

    def get(self, request: Request) -> Response:
        user = request.user

        try:
            profile = StudentProfile.objects.get(user=user)
            passions_count = len(profile.passions) if isinstance(profile.passions, list) else 0
            step1_status = profile.onboarding_step1_status
            bulletins_status = profile.bulletins_status
        except StudentProfile.DoesNotExist:
            step1_status = "pending"
            passions_count = 0
            bulletins_status = "pending"

        try:
            level_profile = StudentLevelProfile.objects.get(profile__user=user)
            step2_status = level_profile.onboarding_step2_status
        except StudentLevelProfile.DoesNotExist:
            step2_status = "pending"

        snap = _SnapAdapter(
            onboarding_step1_status=step1_status,
            passions_count=passions_count,
            onboarding_step2_status=step2_status,
            bulletins_status=bulletins_status,
        )

        level = compute_maturity(snap)

        return Response(
            {
                "level": level.value,
                "next_actions": _next_actions_for(level),
                "computed_at": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )
