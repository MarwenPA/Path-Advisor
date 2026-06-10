"""``GET /api/v1/profile/access-list/`` — Story 1.9 §AC1, §AC6.

Returns the unified list of third parties currently authorized to see the
authenticated student's profile. The endpoint is a thin shell : delegates the
heavy lifting to ``AccessListAggregator`` (composable, testable) and writes
ONE audit row per request (Story 1.7 dedup pattern via ``request._access_list_audit_recorded``).
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsStudent
from apps.profiles.access_list import AccessListAggregator
from apps.profiles.access_list.exceptions import EntryNotFound
from apps.profiles.access_list.revoker import revoke_entry
from apps.profiles.serializers import AccessListEntrySerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def access_list(request: Request) -> Response:
    entries = AccessListAggregator().list_for_user(request.user)
    serialized = AccessListEntrySerializer(entries, many=True).data

    # NFR-S4 — every read of "who sees my data" is itself auditable. Dedup
    # via a per-request flag (Story 1.7 pattern) so a React StrictMode dev
    # double-mount on the page does not double-audit.
    if not getattr(request, "_access_list_audit_recorded", False):
        record_audit(
            action="profile.access_list_read",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject_id=str(request.user.id),
            metadata={"count": len(entries)},
        )
        request._access_list_audit_recorded = True

    return Response({"results": serialized})


_NOT_FOUND_BODY = {
    "type": "https://path-advisor.fr/errors/access-list-entry-not-found",
    "title": "Accès introuvable",
    "status": 404,
    "detail": "Cet accès n'existe pas ou a déjà été révoqué.",
}


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def revoke_access_list_entry(request: Request, entry_id: str) -> Response:
    """Story 1.10 §AC1 — revoke ``entry_id`` for the calling student.

    Optional ``content_hash`` in the POST body is stored in the audit metadata
    for forensic traceability (Story 1.14 pattern : "what did the user actually
    see when they clicked Revoke ?"). The hash is NOT used as a gate — that
    would require pinning the dynamic content (parent email) which makes the
    canonical hash impossible. The hash is proof, not validation.
    """
    body = request.data if isinstance(request.data, dict) else {}
    content_hash = body.get("content_hash")

    try:
        result = revoke_entry(request.user, entry_id, content_hash=content_hash)
    except EntryNotFound:
        return Response(_NOT_FOUND_BODY, status=status.HTTP_404_NOT_FOUND)

    return Response(result)
