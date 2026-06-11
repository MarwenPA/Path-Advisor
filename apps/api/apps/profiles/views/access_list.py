"""``GET /api/v1/profile/access-list/`` + ``POST /<id>/revoke/`` — Stories 1.9 + 1.10
plus review patches P6 P7 P12 P14 P15.

Thin shell endpoints — delegate to ``AccessListAggregator`` (composable,
testable) and ``revoke_entry`` (Story 1.10). All audit + dedup + reason-split
logic lives in those services.
"""

from __future__ import annotations

import logging
import re

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsStudent
from apps.profiles.access_list import AccessListAggregator
from apps.profiles.access_list.aggregator import MAX_ENTRIES, TRUNCATED_FLAG_KEY
from apps.profiles.access_list.exceptions import EntryNotFound
from apps.profiles.access_list.revoker import revoke_entry
from apps.profiles.serializers import AccessListEntrySerializer

log = logging.getLogger(__name__)

#: Review P15 — entry_id format validation. The composite id is
#: ``<source_name>:<source_pk>`` where source_name is `[a-z_]+` and source_pk
#: is alnum + dash + underscore. Anything else (newlines, escape sequences,
#: percent-encoded chars, weird unicode) is 404 before we even touch the DB
#: or the audit log — prevents log-injection via subject_id.
_ENTRY_ID_REGEX = re.compile(r"^[a-z_]+:[A-Za-z0-9_-]{1,64}$")

#: Review P12 — content_hash format validation. SHA-256 hex = 64 chars [a-f0-9].
#: Reject anything else (non-string, malformed, oversize) at the view boundary
#: so the audit metadata stays well-typed.
_CONTENT_HASH_REGEX = re.compile(r"^[a-f0-9]{64}$")


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def access_list(request: Request) -> Response:
    entries = AccessListAggregator().list_for_user(request.user)
    serialized = AccessListEntrySerializer(entries, many=True).data

    # NFR-S4 — every read of "who sees my data" is itself auditable.
    # Review D2 — the per-request flag dedupes DRF intra-request `has_permission`
    # repeats. It does NOT defend against React StrictMode double-mount (two
    # separate HTTP requests = two separate `request` objects). For HTTP-level
    # dedup, a separate cache-bucket strategy would be needed (out of scope).
    if not getattr(request, "_access_list_audit_recorded", False):
        # Review P6 — fail-open on audit-DB outage so a flaky audit table
        # doesn't break the user's RGPD Article 15 right to know who sees
        # their data. The miss is logged for SRE follow-up.
        try:
            record_audit(
                action="profile.access_list_read",
                result=AuditResult.SUCCESS,
                actor=request.user,
                subject_id=str(request.user.id),
                metadata={"count": len(entries)},
            )
        except Exception:
            log.exception(
                "access_list.audit_failed",
                extra={"user_id": request.user.id, "count": len(entries)},
            )
        request._access_list_audit_recorded = True

    # Review P7 — emit `truncated: true` when the aggregator hit the cap.
    body: dict = {"results": serialized}
    if len(entries) >= MAX_ENTRIES:
        body[TRUNCATED_FLAG_KEY] = True
    return Response(body)


_NOT_FOUND_BODY = {
    "type": "https://path-advisor.fr/errors/access-list-entry-not-found",
    "title": "Accès introuvable",
    "status": 404,
    "detail": "Cet accès n'existe pas ou a déjà été révoqué.",
}


def _audit_attempt(user, entry_id: str, *, reason: str) -> None:
    """Mirrors revoker._audit_attempt so the view's early-rejection paths
    (regex fail, malformed content_hash) also get an audit row.
    """
    record_audit(
        action="profile.access_revoke_attempted",
        result=AuditResult.FAILURE,
        actor=user,
        subject_id=entry_id,
        metadata={"reason": reason},
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def revoke_access_list_entry(request: Request, entry_id: str) -> Response:
    """Story 1.10 §AC1 — revoke ``entry_id`` for the calling student.

    Optional ``content_hash`` in the POST body is stored in the audit metadata
    for forensic traceability (Story 1.4 pattern, see review D4). The hash is
    NOT used as a gate but IS validated as `^[a-f0-9]{64}$` (review P12).
    """
    # Review P15 — reject malformed entry_id BEFORE any DB lookup so
    # log-injection / encoded payloads cannot pollute the audit subject_id.
    if not _ENTRY_ID_REGEX.match(entry_id):
        _audit_attempt(request.user, entry_id, reason="malformed_id")
        return Response(_NOT_FOUND_BODY, status=status.HTTP_404_NOT_FOUND)

    body = request.data if isinstance(request.data, dict) else {}
    content_hash = body.get("content_hash")
    # Review P12 — validate format. Reject non-string / wrong-length / non-hex.
    if content_hash is not None and not (
        isinstance(content_hash, str) and _CONTENT_HASH_REGEX.match(content_hash)
    ):
        _audit_attempt(request.user, entry_id, reason="malformed_content_hash")
        return Response(
            {
                "type": "https://path-advisor.fr/errors/content-hash-invalid",
                "title": "Hash de contenu invalide",
                "status": 400,
                "detail": "Le hash fourni n'est pas un SHA-256 hex valide.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = revoke_entry(request.user, entry_id, content_hash=content_hash)
    except EntryNotFound:
        return Response(_NOT_FOUND_BODY, status=status.HTTP_404_NOT_FOUND)

    return Response(result)
