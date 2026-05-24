"""`TenantSessionMiddleware` — sets PostgreSQL session GUCs for RLS policies.

For every request that resolves a Django user, this middleware runs:

    SELECT set_config('app.current_user_id',   '<user.id>',     false),
           set_config('app.current_tenant_id', '<user.tenant>', false),
           set_config('app.actor_role',        '<user.role>',   false);

`is_local=false` (= `SET SESSION`) is used instead of `SET LOCAL` because
Django defaults to autocommit (no `ATOMIC_REQUESTS`): with `SET LOCAL`, the
GUC would be scoped to the implicit one-statement transaction the middleware
opens — by the time the view executes its own queries, the GUC would be
gone. With `SET SESSION` the GUC persists for the lifetime of the connection;
we explicitly `RESET ALL` in the `finally` block to keep `CONN_MAX_AGE > 0`
safe (no leakage to the next request reusing the connection). Post-review
decision D1 (2026-05-24).

Reading these GUCs from the RLS policies (`accounts/0007_enable_rls`) is
what enforces tenant isolation at the DB engine layer — defense in depth
on top of the application's own `.filter(tenant_id=...)` calls.

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
            # 1. Thread-local clear (per-request hygiene — gunicorn thread reuse).
            request_context.clear()
            # 2. PG GUC clear: `RESET ALL` wipes every `set_config(... false)` we
            #    wrote at request entry. Without this, `CONN_MAX_AGE > 0`
            #    connection reuse leaks the previous request's GUCs to the next.
            self._reset_session_context()

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
            raw_id = getattr(user, "id", "") or ""
            user_id = str(raw_id)
            raw_tenant = getattr(user, "tenant_id", None)
            tenant_id = str(raw_tenant) if raw_tenant is not None else ""
            actor_role = str(getattr(user, "role", "") or "")

            # Defensive: an authenticated user without a usable id is a bug
            # — log loudly so the broken auth backend surfaces, but don't
            # bypass: leave the GUC empty so RLS denies (fail-closed).
            if not user_id:
                log.error(
                    "tenant.authenticated_user_without_id",
                    user_repr=repr(user),
                )

        # `is_local=false` (= SET SESSION) — see module docstring for the
        # autocommit rationale (post-review D1).
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT "
                "set_config('app.current_user_id', %s, false), "
                "set_config('app.current_tenant_id', %s, false), "
                "set_config('app.actor_role', %s, false)",
                [user_id, tenant_id, actor_role],
            )

    def _reset_session_context(self) -> None:
        """Clear every `app.*` GUC and any other session-level SET this request made.

        Wrapping in `try/except` keeps a connection drop mid-request from
        masking the original exception. The cleared connection will be torn
        down by Django's `close_old_connections` signal at request end if
        `CONN_MAX_AGE = 0`, so a failed RESET on a broken connection is
        harmless.
        """
        if connection.vendor != "postgresql":
            return
        try:
            with connection.cursor() as cursor:
                cursor.execute("RESET ALL")
        except Exception as exc:
            log.warning(
                "tenant.guc_reset_failed",
                error_type=exc.__class__.__name__,
                error=str(exc),
            )


__all__ = ["TenantSessionMiddleware"]
