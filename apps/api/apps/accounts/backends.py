"""Tenant-aware auth backends — Story 6.5 code-review fix (2026-09).

**Root cause (found via the Story 6.5 Postgres RLS-parity suite — the first
authenticated *admin-write* endpoints ever exercised against real Postgres):**

Every session-authenticated request resolves `request.user` from
`django.contrib.sessions` via `AUTHENTICATION_BACKENDS[i].get_user(user_id)`,
which runs a plain `User.objects.get(pk=user_id)`. `users` is
`FORCE ROW LEVEL SECURITY` (`apps/accounts/migrations/0007_enable_rls.py`)
with a `users_isolation_select` policy keyed on
`id = current_setting('app.current_user_id', true)` — i.e. a user can only
read their OWN row once the GUC is already set to their own id.

But the GUC is set by `TenantSessionMiddleware`
(`path_advisor/middleware/tenant.py`), which itself reads `request.user` to
decide what to set the GUC to — and `TenantSessionMiddleware` runs AFTER
`AuthenticationMiddleware` in `MIDDLEWARE`. The very first read of the lazy
`request.user` (whether by `OTPMiddleware`, by `TenantSessionMiddleware`
itself, or by a view) is what triggers `get_user()` — with no GUC set yet.
Chicken-and-egg: the SELECT needed to know who the user is, is the same
SELECT the RLS policy demands that identity for. Without a bypass, every
authenticated session request on real Postgres silently resolves to
`AnonymousUser` and every protected view 401s.

This mirrors the already-known `force_login()` → `update_last_login`
chicken-egg (session tests wrap that write in `bypass_rls()`) — same shape,
one level up: resolving *who is logged in* can't itself depend on RLS
already knowing who is logged in.

**Fix:** wrap `get_user()` in `bypass_rls()`. This is narrow and safe: the
`user_id` comes from the signed session cookie (server-trusted), never from
request input, and the lookup is a single `pk=` read with no filtering to
bypass — RLS on every OTHER query in the request still applies normally
once `TenantSessionMiddleware` sets the real GUCs immediately after.

Whitelisted call sites (keep in sync with `apps/core/rls.py`'s own list):
1. `TenantAwareModelBackend.get_user` — below.
2. `TenantAwareAllauthBackend.get_user` — below (allauth's backend doesn't
   override `get_user`, but `django.contrib.auth.get_user()` calls
   `load_backend(session_backend_path).get_user(...)` on the SPECIFIC
   backend path stored in the session, so both must be covered or a user
   who logged in via allauth would still 401).
"""

from __future__ import annotations

from allauth.account.auth_backends import AuthenticationBackend as AllauthAuthenticationBackend
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser

from apps.core.rls import bypass_rls


class TenantAwareModelBackend(ModelBackend):
    """`ModelBackend`, with session-user resolution wrapped in `bypass_rls()`."""

    def get_user(self, user_id: str) -> AbstractBaseUser | None:
        with bypass_rls(reason="auth.resolve_session_user"):
            return super().get_user(user_id)


class TenantAwareAllauthBackend(AllauthAuthenticationBackend):
    """allauth's backend, with the same `get_user` fix (see module docstring)."""

    def get_user(self, user_id: str) -> AbstractBaseUser | None:
        with bypass_rls(reason="auth.resolve_session_user"):
            return super().get_user(user_id)


__all__ = ["TenantAwareAllauthBackend", "TenantAwareModelBackend"]
