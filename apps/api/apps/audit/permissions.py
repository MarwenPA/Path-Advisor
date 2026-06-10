"""DRF permission classes for the audit endpoints.

Story 1.7 §AC7 — the generic `IsPathAdmin` lives in `apps.core.permissions`
now. This subclass is kept ONLY for the audit endpoints because Story 1.13
tests assert a specialized `audit.log_query_denied` audit row (DPO triage
signal distinct from the generic `rbac.access_denied`).

Behavior on refusal:
- `rbac.access_denied` audit row written by the core base class (generic).
- `audit.log_query_denied` audit row written by THIS subclass when (and ONLY
  when) the underlying refusal reason was `wrong_role` — code-review P19
  fix: the prior implementation emitted the specialized event for ANY
  refusal, including `not_authenticated` / `not_mfa_verified` paths, which
  produced misleading `reason: not_path_admin` metadata.
- Both deduped per-request via separate flags on `request`.

Use case: an attacker probing the audit endpoint surfaces in BOTH event
streams. DPO queries on `rbac.access_denied` see all escalation attempts;
queries on `audit.log_query_denied` filter to JUST the audit-log probes
caused by wrong role (not auth/MFA failures).

**Deprecation:** code-review P2 — emits `DeprecationWarning` at import-time
to signal the migration to `from apps.core.permissions import IsPathAdmin`.
"""

from __future__ import annotations

import warnings
from typing import Any

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.permissions import IsPathAdmin as _CoreIsPathAdmin

warnings.warn(
    "`apps.audit.permissions.IsPathAdmin` is deprecated as of Story 1.7. "
    "Import from `apps.core.permissions` instead. This shim will be removed "
    "in Sprint 3 cleanup.",
    DeprecationWarning,
    stacklevel=2,
)


class IsPathAdmin(_CoreIsPathAdmin):
    """`apps.core.permissions.IsPathAdmin` + the Story 1.13 specialized
    `audit.log_query_denied` audit row on refusal.

    Tests in `apps/audit/tests/test_views.py` assert the specialized row
    exists exactly once per request — kept here so the contract is intact.

    Code-review P19 — the specialized event fires ONLY when the underlying
    refusal reason was `wrong_role`. For `not_authenticated` (user wasn't
    logged in) or `not_mfa_verified` (user is path_admin but no MFA), the
    generic `rbac.access_denied` row suffices ; emitting the specialized
    event with `reason: not_path_admin` would be a misleading DPO signal.
    """

    message = "Vous n'avez pas l'autorisation d'accéder au journal d'audit."

    def has_permission(self, request: Any, view: Any) -> bool:
        allowed = super().has_permission(request, view)
        if allowed:
            return True

        user = getattr(request, "user", None)
        is_authenticated = user is not None and getattr(user, "is_authenticated", False)
        actor_role = getattr(user, "role", "") if is_authenticated else ""

        # Code-review P19 — only emit the specialized event when the refusal
        # was actually a role mismatch (an authenticated non-path_admin user).
        # The base class already wrote `rbac.access_denied` with the precise
        # reason ; the specialized event was historically meant for
        # `not_path_admin` audit-log queries.
        is_wrong_role = is_authenticated and actor_role != "path_admin"
        if not is_wrong_role:
            return False

        if not getattr(request, "_audit_log_denial_recorded", False):
            record_audit(
                action="audit.log_query_denied",
                result=AuditResult.DENIED,
                actor=user,
                metadata={
                    "reason": "not_path_admin",
                    "user_role": actor_role or "",
                    "view": view.__class__.__name__ if view is not None else "",
                },
            )
            request._audit_log_denial_recorded = True
        return False
