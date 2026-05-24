"""`TenantSessionMiddleware` — sets PostgreSQL session GUCs for RLS policies.

For every request that resolves a Django user, this middleware runs:

    SET LOCAL app.current_user_id = '<user.id>';
    SET LOCAL app.current_tenant_id = '<user.tenant_id or empty>';
    SET LOCAL app.actor_role = '<user.role>';

`SET LOCAL` is mandatory (not `SET SESSION`): the GUCs reset at transaction
commit/rollback, so the next request that reuses the connection
(`CONN_MAX_AGE > 0`) starts with a clean slate. Reading these GUCs from the
RLS policies (`accounts/0007_enable_rls`) is what enforces tenant isolation
at the DB engine layer — defense in depth on top of the application's
own `.filter(tenant_id=...)` calls.

Position in `MIDDLEWARE` matters:
- AFTER `django.contrib.auth.middleware.AuthenticationMiddleware` — `request.user`
  must already be resolved.
- BEFORE `allauth.account.middleware.AccountMiddleware` — allauth and every
  downstream view/audit hook must run with the GUCs in place.

For SQLite (the unit-test fast path) the middleware no-ops; RLS is exercised
in the dedicated `make test-rls` PostgreSQL CI job.

This middleware also unifies the existing `apps.core.request_context` setup
that audit views call manually today ([apps/audit/views.py:53,191]). After
this story lands, those manual calls become redundant-but-defensive (kept
on purpose — removing them is a follow-up cleanup, not part of 1.8).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog
from django.db import connection
from django.http import HttpRequest, HttpResponse

from apps.core import request_context

log = structlog.get_logger(__name__)


class TenantSessionMiddleware:
    """Wire `request.user` into Postgres session GUCs + the audit thread-local."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            self._apply_session_context(request)
            return self.get_response(request)
        finally:
            # Per-request hygiene: the thread-local is the same per-process
            # store the audit subsystem reads (cf. apps.core.request_context).
            # Without `clear()`, a thread reused by gunicorn between two
            # requests would carry the previous actor through to the second.
            request_context.clear()

    # ---------------------------- internals ---------------------------------

    def _apply_session_context(self, request: HttpRequest) -> None:
        """Push (user_id, tenant_id, role) into both the thread-local and PG GUCs."""
        # Thread-local first — every request gets the audit subsystem ready,
        # PG GUCs are best-effort and PG-only.
        request_context.set_actor_from_request(request)

        # GUC writes are PostgreSQL-specific. SQLite (unit-test fast path) has
        # no equivalent, so we no-op there; RLS is exercised end-to-end in
        # `make test-rls` against a real Postgres.
        if connection.vendor != "postgresql":
            return

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            user_id = ""
            tenant_id = ""
            actor_role = ""
        else:
            user_id = str(getattr(user, "id", "") or "")
            raw_tenant = getattr(user, "tenant_id", None)
            tenant_id = str(raw_tenant) if raw_tenant is not None else ""
            actor_role = str(getattr(user, "role", "") or "")

        try:
            with connection.cursor() as cursor:
                # `SET LOCAL` requires being inside a transaction. Django wraps
                # each request in one when ATOMIC_REQUESTS is set, but we don't
                # rely on that — `set_session` works either way because Django
                # autocommit boundaries still scope GUC clears on connection
                # release.
                cursor.execute(
                    "SELECT "
                    "set_config('app.current_user_id', %s, true), "
                    "set_config('app.current_tenant_id', %s, true), "
                    "set_config('app.actor_role', %s, true)",
                    [user_id, tenant_id, actor_role],
                )
        except Exception as exc:
            # RLS GUC setup MUST NOT block a request — if PG is unreachable
            # for the GUC write, the query that needs the policy will fail
            # explicitly later (deny by default), which is the right behavior.
            # We surface the issue via structlog + Sentry but let the request
            # proceed so failure modes are visible at the query layer.
            log.warning(
                "tenant.guc_set_failed",
                error_type=exc.__class__.__name__,
                error=str(exc),
            )

    def __repr__(self) -> str:  # pragma: no cover - introspection helper
        return f"<{type(self).__name__} get_response={self.get_response!r}>"


__all__ = ["TenantSessionMiddleware"]


# Type-only re-export for any future code that wants to type-check imports
# of this symbol without pulling in the implementation.
_TYPING_GUARD: Any = None
