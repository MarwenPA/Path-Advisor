"""DRF permission classes for the audit endpoints.

`IsPathAdmin` gates `/api/v1/audit/logs/`. A refusal triggers a `denied`
entry in the journal itself — the meta-audit promised by Story 1.13 §AC5.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult


class IsPathAdmin(BasePermission):
    """Only `path_admin` users (or superusers) may read the audit log.

    Failures emit a typed `InsufficientPermissions` Problem Details and
    record a single `audit.log_query_denied` row per request (DRF may invoke
    `has_permission` multiple times — list view + filter backends — so we
    cache the denial flag on the request object to avoid log amplification).
    """

    message = "Vous n'avez pas l'autorisation d'accéder au journal d'audit."

    def has_permission(self, request: Any, view: Any) -> bool:
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        # Superusers always pass — otherwise they get audited as "denied" which is noise.
        if getattr(user, "is_superuser", False):
            return True
        if getattr(user, "role", None) == "path_admin":
            return True

        # Authenticated but wrong role → 403 + RFC 7807 Problem Details (raised by the view
        # via `permission_denied_message`) + ONE audit row per request.
        if not getattr(request, "_audit_log_denial_recorded", False):
            record_audit(
                action="audit.log_query_denied",
                result=AuditResult.DENIED,
                actor=user,
                metadata={
                    "reason": "not_path_admin",
                    "user_role": getattr(user, "role", "") or "",
                    "view": view.__class__.__name__,
                },
            )
            request._audit_log_denial_recorded = True
        return False
