"""Onboarding step-1 endpoints (Story 2.1 AC5, AC6, AC10).

- `GET /api/v1/students/me/onboarding/passions` — read the current profile.
  Returns 200 with empty defaults if the profile doesn't exist yet (the row
  is created lazily on first PATCH).
- `PATCH /api/v1/students/me/onboarding/passions` — apply one sub-step at a
  time. Creates the profile row on first call. Idempotent — re-sending the
  same payload returns the same shape.

Auth: any authenticated user. The role gate (student vs counselor vs parent)
is intentionally NOT enforced here at MVP — the route is meant to be
unreachable by non-students via the frontend routing. Story 1.7 (RBAC
middleware) will tighten this. For non-student authenticated users that DO
reach the endpoint, the operation is technically allowed but only mutates
their own profile (RLS guards data leakage), which is a niche misuse.

Tenant isolation: relies on `TenantSessionMiddleware` (Story 1.8) having
already set `app.current_user_id` so the RLS policy on `student_profiles`
limits reads/writes to the caller's row.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.students.models import StudentProfile
from apps.students.serializers import (
    OnboardingStep1PatchSerializer,
    OnboardingStep1ReadSerializer,
)


class OnboardingPassionsView(APIView):
    """GET + PATCH `/api/v1/students/me/onboarding/passions`.

    The plural endpoint name reflects the historical naming: this is the
    canonical step-1 entry point, not just the passions sub-step. The
    `step` discriminator inside the PATCH payload selects which sub-step
    is being submitted.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        profile = self._get_or_none(request)
        if profile is None:
            return Response(self._empty_payload(), status=status.HTTP_200_OK)
        return Response(OnboardingStep1ReadSerializer(profile).data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        serializer = OnboardingStep1PatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = self._get_or_create(request)
        serializer.apply(profile)
        profile.save()

        return Response(OnboardingStep1ReadSerializer(profile).data, status=status.HTTP_200_OK)

    # --- helpers --------------------------------------------------------

    @staticmethod
    def _get_or_none(request: Request) -> StudentProfile | None:
        # RLS reduces the queryset to the caller's own row automatically. The
        # extra .filter(user=request.user) is application-layer defense-in-depth
        # for SQLite (which has no RLS) and clarity at the call site.
        return StudentProfile.objects.filter(user=request.user).first()

    @staticmethod
    def _get_or_create(request: Request) -> StudentProfile:
        profile = StudentProfile.objects.filter(user=request.user).first()
        if profile is not None:
            return profile
        # Lazy creation: tenant_id is filled by `StudentProfile.save()` from
        # the user's tenant_id. Status starts at `pending` and the first
        # sub-step PATCH bumps it to `in_progress` (see serializer.apply).
        profile = StudentProfile(user=request.user)
        profile.save()
        return profile

    @staticmethod
    def _empty_payload() -> dict[str, Any]:
        """Default shape for a user with no profile row yet (AC5 first-load case)."""
        return {
            "passions": [],
            "valeurs": [],
            "interets": {"1": None, "2": None, "3": None},
            "onboarding_step1_status": "pending",
            "onboarding_step1_completed_at": None,
        }
