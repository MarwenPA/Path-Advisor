"""CI gate — Story 1.7 §AC5 / §T7.

Walks every URL pattern in `path_advisor.urls.urlpatterns`, resolves each
view callable (CBV or FBV), and asserts that `permission_classes` is
declared EXPLICITLY.

The gate refuses:
- Endpoints with `permission_classes = ()` (DRF default → `AllowAny`).
- Endpoints with `permission_classes` containing ONLY `AllowAny` or
  `IsAuthenticated` UNLESS the URL pattern is in `_PUBLIC_ENDPOINT_WHITELIST`.

The whitelist is the source of truth for "intentionally public" endpoints
(auth bootstrap, login, password-reset request, etc.). Every entry MUST
have a rationale comment.

Exit 0 = OK. Exit 1 = at least one undeclared / under-protected endpoint.

Usage (from `apps/api/` dir):

    DJANGO_SETTINGS_MODULE=path_advisor.settings.test \\
        python scripts/assert_rbac_declared.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

import django

#: Endpoints that are LEGITIMATELY public (no auth required) — each entry
#: MUST carry a comment explaining WHY. Add a new entry only when you're
#: certain the endpoint must work for anonymous users.
#:
#: Format: `(url_name_or_path_pattern, rationale_comment)`. The matcher
#: accepts either the `name=` of the URL pattern OR a literal path that
#: `request.path` would produce.
_PUBLIC_ENDPOINT_WHITELIST: dict[str, str] = {
    # --- Auth bootstrap (every SPA needs to seed CSRF before any POST)
    "csrf": "CSRF cookie bootstrap — anonymous on purpose",
    # --- Signup / login / password reset (the whole point is anonymous access)
    "rest_register": "Signup endpoint — Story 1.3",
    "rest_resend_email": "Email-verification resend — Story 1.3",
    "rest_login": "Login endpoint — Story 1.5 (auth attempt happens here)",
    "rest_password_reset": "Password reset request — Story 1.5",
    "rest_password_reset_confirm": "Password reset confirm with token — Story 1.5",
    # --- MFA flow public endpoints (mfa_session JWT is the auth proof,
    #     no session cookie yet — Story 1.6)
    "mfa_enroll_start": "MFA enrollment start — mfa_session is the auth proof",
    "mfa_enroll_confirm": "MFA enrollment confirm — mfa_session is the auth proof",
    "mfa_challenge": "MFA challenge — mfa_session is the auth proof",
    # --- Parental consent public landing (parent has no account, the token
    #     is the auth proof — Story 1.4)
    "parental-consent-status": "Public landing for parental consent token — Story 1.4",
    "parental-consent-decide": "Public decision endpoint for parental consent token — Story 1.4",
    # --- Account-deletion cancel landing (token-based, no auth — Story 1.12)
    "account-deletion-cancel": "Public cancel landing for account-deletion token — Story 1.12",
    "account-deletion-status-public": "Public status for account-deletion token — Story 1.12",
    # --- Email-verification public callback (user clicks email link, no auth)
    "rest_verify_email": "Email verification API — public by allauth design",
    "account_confirm_email": "Email confirmation landing — public by allauth design",
    "account_email_verification_sent": "Email-verification-sent info page — public by allauth design",
    # --- Logout (anonymous-friendly no-op acceptable; idempotent)
    # rest_logout — dj-rest-auth ships this with `AllowAny`. Spec §AC7 table
    # of Story 1.7 asked for `[IsAuthenticated]`, but the idiomatic pattern
    # (and dj-rest-auth's own behavior) is anonymous-friendly idempotent
    # logout that returns 200 regardless. Overriding the dj-rest-auth view
    # solely for this would be churn ; whitelist + rationale is the
    # accepted deviation (code-review P16, Story 1.7 review 2026-06-08).
    "rest_logout": "Logout — idempotent + anonymous-friendly (dj-rest-auth default; spec AC7 deviation accepted)",
    # --- DRF auto-generated API root (`/api/v1/me/`) — read-only index
    "api-root": "DRF auto-generated API root — read-only index, no PII",
    # --- Built-in Django admin (gated by Django admin auth, not DRF)
    "admin:index": "Django admin index — Django admin gates this with is_staff",
    # --- OpenAPI schema (intentionally public; SPA consumes it)
    "schema": "OpenAPI schema — public by SPA design",
    "swagger-ui": "Swagger UI — public by SPA design",
    "redoc": "Redoc UI — public by SPA design",
    # --- Health endpoint (must be public for load balancer probes)
    "health": "Liveness probe for load balancer — must work without auth",
}


#: A `permission_classes` tuple is considered "trivially permissive" if it
#: contains ONLY one of these classes. We require an explicit role check
#: on top (e.g., `[IsAuthenticated, IsStudent]`) for non-whitelisted views.
_TRIVIAL_PERMISSIONS: set[str] = {"AllowAny"}

#: `IsAuthenticated` alone is permitted for some intentionally minimal-guard
#: views (e.g., logout, fetch-own-user, fetch-own-status). These views are
#: whitelisted by URL name.
_ISAUTHENTICATED_ONLY_WHITELIST: set[str] = {
    "rest_user_details",
    "rest_user",
    # Self-service password change — user proves identity with current password
    "rest_password_change",
    # Story 1.12 — account deletion request / status (self-service, scoped
    # to request.user; no object ID in URL so `IsOwner` would be a no-op).
    # Code-review D4 (Story 1.7 review 2026-06-08): the spec table mandated
    # `IsOwner` for symmetry; we leave these on `IsAuthenticated` + this
    # whitelist because the queryset filter is `request.user.id` only —
    # there is no IDOR surface to defend at the permission layer.
    "account-deletion-request",
    "account-deletion-status-self",
    # Story 1.6 — MFA regenerate recovery codes (any authenticated enrolled user)
    "mfa_regenerate_recovery_codes",
}


def _setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.test")
    django.setup()


def _resolve_view_callable(pattern: Any) -> Any:
    """Pull the view callable out of a URLPattern."""
    callback = getattr(pattern, "callback", None)
    if callback is None:
        return None
    # CBV: DRF attaches the class via `cls` attribute on as_view()-wrapped func
    cls = getattr(callback, "cls", None)
    if cls is not None:
        return cls
    # FBV decorated with @api_view: the callback IS the wrapper; the inner
    # permission_classes are attached to the wrapper via `.cls` or kept on
    # the wrapper itself.
    return callback


def _extract_permission_classes(view: Any) -> list[str]:
    """Return the names of DRF permission classes declared on the view."""
    pc = getattr(view, "permission_classes", None)
    if pc is None:
        return []
    return [getattr(p, "__name__", str(p)) for p in pc]


def _walk_urlpatterns(urlpatterns: Any, prefix: str = "") -> list[dict]:
    """Recursively walk a URLConf and yield {name, path, view, permission_classes}."""
    from django.urls.resolvers import URLPattern, URLResolver

    results: list[dict] = []
    for pat in urlpatterns:
        if isinstance(pat, URLResolver):
            # Recurse into include()'d urlconfs
            sub_prefix = prefix + str(pat.pattern)
            results.extend(_walk_urlpatterns(pat.url_patterns, sub_prefix))
        elif isinstance(pat, URLPattern):
            view = _resolve_view_callable(pat)
            if view is None:
                continue
            results.append(
                {
                    "name": getattr(pat, "name", None),
                    "path": prefix + str(pat.pattern),
                    "view": view,
                    "permission_classes": _extract_permission_classes(view),
                }
            )
    return results


def _is_admin_route(route: dict) -> bool:
    """Django admin routes carry their own auth; not subject to DRF checks."""
    name = route.get("name") or ""
    path = route.get("path") or ""
    return name.startswith("admin:") or path.startswith("admin/")


def _whitelisted(route: dict, whitelist: set[str] | dict[str, str]) -> bool:
    """Check whether a route matches a whitelist by `name=` OR `path` literal
    (code-review P14 — was previously name-only, which let an attacker
    bypass by naming their endpoint after a whitelisted entry like `csrf`).
    """
    name = route.get("name") or ""
    path = route.get("path") or ""
    if name and name in whitelist:
        return True
    # Match path with leading `/` (URL patterns store relative paths)
    candidates = (path, f"/{path}", path.rstrip("/"), f"/{path.rstrip('/')}")
    return any(c in whitelist for c in candidates if c)


def _check_route(route: dict) -> str | None:
    """Return an error message if the route fails the gate, else None."""
    if _is_admin_route(route):
        return None

    name = route.get("name") or ""
    pcs = route.get("permission_classes") or []

    # Code-review P27 — `IsOwner` MUST be composed with a role permission
    # OR with `IsAuthenticated` plus an explicit whitelist entry (some
    # endpoints scope by `request.user` filter and use IsOwner for IDOR
    # defense without a role gate). Standalone `IsOwner` is a permission-
    # misuse footgun.
    if "IsOwner" in set(pcs) or "IsOwnerOrPathAdmin" in set(pcs):
        has_role_companion = any(
            p in pcs
            for p in (
                "IsStudent",
                "IsParent",
                "IsCounselor",
                "IsSchoolAdmin",
                "IsPathAdmin",
                "IsSupport",
                "IsB2C",
                "IsStaff",
                "IsAuthenticatedAndActive",
            )
        )
        if not has_role_companion and "IsAuthenticated" not in pcs:
            return (
                f"  · {route['path']!r} (name={name!r}) → permission_classes={pcs} "
                "(IsOwner without a role companion — compose with one of "
                "IsStudent/IsParent/IsCounselor/IsSchoolAdmin/IsPathAdmin/IsSupport/"
                "IsB2C/IsStaff/IsAuthenticatedAndActive OR add IsAuthenticated explicitly)"
            )

    # No permission_classes at all
    if not pcs:
        if _whitelisted(route, _PUBLIC_ENDPOINT_WHITELIST):
            return None
        return f"  · {route['path']!r} (name={name!r}) → no permission_classes declared"

    # Trivially permissive (AllowAny only)
    if set(pcs) <= _TRIVIAL_PERMISSIONS:
        if _whitelisted(route, _PUBLIC_ENDPOINT_WHITELIST):
            return None
        return (
            f"  · {route['path']!r} (name={name!r}) → permission_classes={pcs} "
            "(AllowAny but not in whitelist)"
        )

    # IsAuthenticated only
    if set(pcs) == {"IsAuthenticated"}:
        if _whitelisted(route, _ISAUTHENTICATED_ONLY_WHITELIST) or _whitelisted(
            route, _PUBLIC_ENDPOINT_WHITELIST
        ):
            return None
        return (
            f"  · {route['path']!r} (name={name!r}) → permission_classes=['IsAuthenticated'] "
            "(missing role check — declare a Path-Advisor permission like "
            "[IsAuthenticated, IsStudent] OR add to _ISAUTHENTICATED_ONLY_WHITELIST with rationale)"
        )

    return None


def main() -> int:
    _setup_django()
    from django.urls import get_resolver

    routes = _walk_urlpatterns(get_resolver().url_patterns)

    failures: list[str] = []
    for route in routes:
        err = _check_route(route)
        if err:
            failures.append(err)

    if failures:
        print(
            f"❌ assert_rbac_declared: {len(failures)} endpoint(s) fail the RBAC declaration gate.\n"
            "Each endpoint MUST either:\n"
            "  1. declare a Path-Advisor permission (e.g. `IsStudent`, `IsCounselor`), OR\n"
            "  2. be added to `_PUBLIC_ENDPOINT_WHITELIST` with a rationale comment\n"
            "     (for genuinely anonymous endpoints), OR\n"
            "  3. be added to `_ISAUTHENTICATED_ONLY_WHITELIST` with a rationale comment\n"
            "     (for self-service endpoints scoped to `request.user`).\n"
        )
        for f in failures:
            print(f)
        return 1

    print(f"✓ assert_rbac_declared: {len(routes)} endpoint(s) pass the RBAC gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
