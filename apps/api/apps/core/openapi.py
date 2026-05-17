"""drf-spectacular hooks shared across the API."""

from __future__ import annotations

from typing import Any

# Paths whose response schema cannot be inspected while `TOKEN_MODEL=None`. They
# are functional at runtime (session cookies) but invisible in the OpenAPI export
# until Story 1.5 ships a Path-Advisor `@extend_schema` for each.
_EXCLUDED_PATHS = frozenset(
    {
        "/api/v1/auth/login/",
        "/api/v1/auth/logout/",
        "/api/v1/auth/password/change/",
        "/api/v1/auth/password/reset/",
        "/api/v1/auth/password/reset/confirm/",
        "/api/v1/auth/user/",
    }
)


def exclude_token_endpoints(endpoints: list[tuple[str, Any, str, Any]], **kwargs: Any) -> list:
    """Drop endpoints whose generated response references dj-rest-auth's `TokenSerializer`."""
    return [tup for tup in endpoints if tup[0] not in _EXCLUDED_PATHS]
