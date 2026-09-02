"""Establishments app views — Story 6.5 §T4/§T5.

Admin (write) endpoints — first admin-write endpoints in the repo:
  POST /api/v1/admin/establishments/                                — AC1
  GET  /api/v1/admin/establishments/                                — list
  POST /api/v1/admin/establishments/{establishment_id}/cohorts/     — AC2
  POST /api/v1/admin/cohorts/{cohort_id}/import-csv/                — AC3
  GET  /api/v1/admin/cohorts/{cohort_id}/import-jobs/{job_id}/      — AC3 poll
  POST /api/v1/admin/establishments/{establishment_id}/counselors/  — AC4

Public acceptance endpoints (`AllowAny` — token is the auth proof):
  GET  /api/v1/auth/counselor-invitation/{token}/          — AC4
  POST /api/v1/auth/counselor-invitation/{token}/accept/   — AC4
  GET  /api/v1/students/invitation/{token}/                — AC5
  POST /api/v1/students/invitation/{token}/accept/         — AC5
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAuthenticatedAndActive, IsPathAdmin
from apps.establishments.exceptions import CsvTooManyRows
from apps.establishments.models import CohortImportJob, Establishment
from apps.establishments.serializers import (
    CohortCreateSerializer,
    CohortImportJobSerializer,
    CohortSerializer,
    CounselorInvitationAcceptSerializer,
    CounselorInvitationCreateSerializer,
    CounselorInvitationSerializer,
    EstablishmentCreateSerializer,
    EstablishmentSerializer,
    StudentInvitationAcceptSerializer,
    StudentInvitationPublicSerializer,
)
from apps.establishments.services.cohort import create_cohort
from apps.establishments.services.counselor_invitation import (
    accept_invitation as accept_counselor_invitation,
)
from apps.establishments.services.counselor_invitation import (
    create_counselor_invitation,
)
from apps.establishments.services.counselor_invitation import (
    get_invitation_by_token as get_counselor_invitation_by_token,
)
from apps.establishments.services.establishment import create_establishment
from apps.establishments.services.student_import import parse_csv_rows
from apps.establishments.services.student_import_invitation import (
    accept_invitation as accept_student_invitation,
)
from apps.establishments.services.student_import_invitation import (
    get_invitation_by_token as get_student_invitation_by_token,
)

_CSV_MAX_ROWS = 2000


class EstablishmentListCreateView(APIView):
    """POST/GET /api/v1/admin/establishments/ — AC1."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request) -> Response:
        establishments = Establishment.objects.order_by("-created_at")
        return Response(EstablishmentSerializer(establishments, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = EstablishmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        establishment = create_establishment(**serializer.validated_data)
        return Response(EstablishmentSerializer(establishment).data, status=status.HTTP_201_CREATED)


class EstablishmentCohortListCreateView(APIView):
    """POST /api/v1/admin/establishments/{establishment_id}/cohorts/ — AC2."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def post(self, request: Request, establishment_id: str) -> Response:
        establishment = get_object_or_404(Establishment, id=establishment_id)
        serializer = CohortCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # `Cohort` is a `TenantScopedModel` — its fail-loud `save()` needs an
        # actor in `apps.core.request_context`. `ActorContextMiddleware`
        # already sets this from the plain Django `request.user` at the
        # start of the request; this explicit set is a defensive no-op in
        # production and the only thing that makes it work under DRF's
        # `force_authenticate()` test helper, which only patches the
        # DRF-wrapped `request.user` (read here), not the raw Django one
        # the middleware reads earlier in the chain.
        from apps.core import request_context

        request_context.set_actor(request.user)
        cohort = create_cohort(establishment=establishment, **serializer.validated_data)
        return Response(CohortSerializer(cohort).data, status=status.HTTP_201_CREATED)


class CohortImportCsvView(APIView):
    """POST /api/v1/admin/cohorts/{cohort_id}/import-csv/ — AC3."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request: Request, cohort_id: str) -> Response:
        from apps.establishments.models import Cohort

        cohort = get_object_or_404(Cohort, id=cohort_id)
        file_obj = request.data.get("file")
        if file_obj is None:
            return Response({"detail": "Fichier CSV requis."}, status=status.HTTP_400_BAD_REQUEST)

        rows = parse_csv_rows(file_obj.read())
        if len(rows) > _CSV_MAX_ROWS:
            raise CsvTooManyRows()

        from django.db import transaction

        from apps.establishments.tasks import process_cohort_import

        with transaction.atomic():
            job = CohortImportJob.objects.create(
                cohort=cohort,
                uploaded_by=request.user,
                total_rows=len(rows),
            )
            transaction.on_commit(lambda: process_cohort_import.delay(job.id, rows))

        return Response({"job_id": job.id, "status": job.status}, status=status.HTTP_202_ACCEPTED)


class CohortImportJobDetailView(APIView):
    """GET /api/v1/admin/cohorts/{cohort_id}/import-jobs/{job_id}/ — AC3 poll."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request: Request, cohort_id: str, job_id: str) -> Response:
        job = get_object_or_404(CohortImportJob, id=job_id, cohort_id=cohort_id)
        return Response(CohortImportJobSerializer(job).data)


class EstablishmentCounselorListCreateView(APIView):
    """POST /api/v1/admin/establishments/{establishment_id}/counselors/ — AC4."""

    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def post(self, request: Request, establishment_id: str) -> Response:
        establishment = get_object_or_404(Establishment, id=establishment_id)
        serializer = CounselorInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = create_counselor_invitation(
            establishment=establishment, **serializer.validated_data
        )
        return Response(
            CounselorInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED
        )


# ---------------------------------------------------------------------------
# Public acceptance endpoints — AllowAny, token is the auth proof.
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([AllowAny])
def counselor_invitation_status(request: Request, token: str) -> Response:
    invitation = get_counselor_invitation_by_token(token)
    return Response(
        {
            "establishment_name": invitation.establishment.name,
            "email": invitation.email,
            "status": invitation.status,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def counselor_invitation_accept(request: Request, token: str) -> Response:
    invitation = get_counselor_invitation_by_token(token)
    serializer = CounselorInvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    accept_counselor_invitation(
        invitation=invitation, password=serializer.validated_data["password"]
    )
    # No auto-login (story §AC4 second clause) — requires_mfa=True from
    # creation means the normal login+MFA-enrollment flow must run.
    return Response({"detail": "Invitation acceptée — connecte-toi pour continuer."})


@api_view(["GET"])
@permission_classes([AllowAny])
def student_invitation_status(request: Request, token: str) -> Response:
    invitation = get_student_invitation_by_token(token)
    return Response(
        StudentInvitationPublicSerializer(
            {
                "establishment_name": invitation.cohort.establishment.name,
                "status": invitation.status,
            }
        ).data
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def student_invitation_accept(request: Request, token: str) -> Response:
    invitation = get_student_invitation_by_token(token)
    serializer = StudentInvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    student = accept_student_invitation(
        invitation=invitation, password=serializer.validated_data["password"]
    )
    return Response({"detail": "Mot de passe défini.", "status": student.status})
