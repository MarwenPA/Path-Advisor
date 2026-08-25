"""Family app views — Story 6.1 §T3.

- `POST /api/v1/family/parent-invitations/` — élève invites a parent (AC1/AC2)
- `GET /api/v1/family/parent-invitations/` — élève's own "Mes proches" list
- `GET /api/v1/family/parent-invitations/{token}/` — public read (AC3)
- `POST /api/v1/family/parent-invitations/{token}/accept/` — anonymous OR
  already-authenticated `role="parent"` accept (AC3/AC4)
- `POST /api/v1/family/parent-invitations/{invitation_id}/resend/` — owner-only
"""

from __future__ import annotations

from django.contrib.auth import login as django_login
from drf_spectacular.utils import extend_schema
from rest_framework import status as drf_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import UserRole
from apps.core.permissions import IsStudent
from apps.core.rls import bypass_rls
from apps.core.text import mask_email
from apps.family.exceptions import ParentInvitationNotFoundOrExpired
from apps.family.models import ParentInvitation, ParentInvitationStatus
from apps.family.serializers import (
    ParentInvitationAcceptSerializer,
    ParentInvitationCreateSerializer,
    ParentInvitationListItemSerializer,
    ParentInvitationPublicSerializer,
)
from apps.family.services.parent_invitation import (
    accept_invitation,
    create_invitation,
    get_invitation_by_token,
    resend_invitation,
)


@extend_schema(
    summary="Create (POST, AC1) or list (GET, T3.5) my parent invitations",
    request=ParentInvitationCreateSerializer,
    responses={
        200: ParentInvitationListItemSerializer(many=True),
        201: ParentInvitationListItemSerializer,
        409: None,
    },
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsStudent])
def parent_invitations_collection(request: Request) -> Response:
    if request.method == "POST":
        serializer = ParentInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = create_invitation(
            student=request.user,
            parent_email=serializer.validated_data["parent_email"],
            relationship=serializer.validated_data.get("relationship"),
            custom_message=serializer.validated_data.get("custom_message"),
        )
        return Response(
            ParentInvitationListItemSerializer(invitation).data,
            status=drf_status.HTTP_201_CREATED,
        )

    invitations = ParentInvitation.objects.filter(student=request.user).order_by("-created_at")
    return Response(ParentInvitationListItemSerializer(invitations, many=True).data)


def _status_label(invitation: ParentInvitation) -> str:
    if invitation.status == ParentInvitationStatus.PENDING and invitation.is_expired:
        return ParentInvitationStatus.EXPIRED
    return invitation.status


@extend_schema(
    summary="Read a parent-invitation token's public state (AC3)",
    responses={200: ParentInvitationPublicSerializer, 404: None},
    auth=[],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def parent_invitation_status(request: Request, token: str) -> Response:
    with bypass_rls(
        reason="parent_invitation.status_read",
        metadata={"token_prefix": token[:8] if token else ""},
    ):
        invitation = get_invitation_by_token(token)
        payload = {
            "student_first_name": invitation.student.email.split("@")[0],
            "student_masked_email": mask_email(invitation.student.email),
            "parent_email": invitation.parent_email,
            "relationship": invitation.relationship,
            "custom_message": invitation.custom_message,
            "status": _status_label(invitation),
        }
    return Response(ParentInvitationPublicSerializer(payload).data)


@extend_schema(
    summary="Accept a parent invitation — creates an account or links a second child (AC3/AC4)",
    request=ParentInvitationAcceptSerializer,
    responses={200: None, 404: None, 409: None},
    auth=[],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def parent_invitation_accept(request: Request, token: str) -> Response:
    serializer = ParentInvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with bypass_rls(
        reason="parent_invitation.accept",
        metadata={"token_prefix": token[:8] if token else ""},
    ):
        invitation = ParentInvitation.objects.filter(token=token).select_related("student").first()
        if invitation is None:
            raise ParentInvitationNotFoundOrExpired()

        # AC4 — an already-authenticated `role="parent"` user just adds a link,
        # ignoring the account-creation fields in the body.
        existing_user = None
        if request.user.is_authenticated and request.user.role == UserRole.PARENT:
            existing_user = request.user

        parent_user = accept_invitation(
            invitation=invitation,
            existing_user=existing_user,
            email=serializer.validated_data.get("email"),
            password=serializer.validated_data.get("password"),
            first_name=serializer.validated_data.get("first_name"),
            last_name=serializer.validated_data.get("last_name"),
        )

    if existing_user is None:
        # AC3 — auto-login the newly created parent (Story 1.5 session pattern).
        # The request is still anonymous (the parent had no account until a
        # moment ago), so `update_last_login` would UPDATE `users` outside any
        # `app.current_user_id` GUC and be denied by the Story 1.8 RLS modify
        # policy ("Save … did not affect any rows"). The account was itself
        # created under `bypass_rls` above — stamping its `last_login` at
        # first login is part of the same system-driven activation, so the
        # bypass is legitimate here too.
        with bypass_rls(reason="parent_invitation.accept_autologin"):
            django_login(request, parent_user, backend="django.contrib.auth.backends.ModelBackend")

    return Response({"detail": "Invitation acceptée.", "role": parent_user.role})


@extend_schema(
    summary="Resend a pending parent invitation (owner-only) — AC2",
    responses={200: None, 404: None, 429: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def parent_invitation_resend(request: Request, invitation_id: str) -> Response:
    invitation = ParentInvitation.objects.filter(
        id=invitation_id,
        student=request.user,
        status=ParentInvitationStatus.PENDING,
    ).first()
    if invitation is None:
        raise ParentInvitationNotFoundOrExpired()
    resend_invitation(invitation=invitation)
    return Response({"detail": "Invitation renvoyée."})
