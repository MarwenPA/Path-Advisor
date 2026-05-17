"""Thread-local store for the current request's actor — used by `apps.audit.decorators`.

Why a thread-local?
- The `@audit_action` decorator wraps service functions that have no `request`
  in their signature. We need a way for them to know who's calling, without
  threading the request through every layer.
- Each Django request runs on a single thread (sync), so a thread-local is safe.
- Story 1.7 will introduce a middleware that calls `set_actor_from_request` at
  the start of each request and `clear()` in `process_response`. For Story 1.13
  the wiring is explicit on the audit endpoints (T5.7).

Usage:
    from apps.core import request_context

    @decorator_or_middleware
    def some_view(request):
        request_context.set_actor_from_request(request)
        try:
            ...
        finally:
            request_context.clear()
"""

from __future__ import annotations

import hashlib
import threading
from typing import Any

from django.conf import settings

_local = threading.local()


def set_actor_from_request(request: Any) -> None:
    """Capture actor + request metadata from a DRF/Django request."""
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        actor_id = getattr(user, "id", None)
        _local.actor_id = str(actor_id) if actor_id is not None else None
        _local.actor_role = getattr(user, "role", "") or ""
        _local.tenant_id = getattr(user, "tenant_id", None)
    else:
        _local.actor_id = None
        _local.actor_role = ""
        _local.tenant_id = None

    _local.request_id = request.headers.get("X-Request-Id") if hasattr(request, "headers") else None
    ip = _client_ip(request)
    # Bind IP hash to the actor's tenant so identical IPs across tenants get
    # different hashes (Story 1.13 §4.9 — prevents cross-tenant correlation).
    _local.ip_hash = _hash_ip(ip, _local.tenant_id) if ip else None
    _local.user_agent = (
        request.headers.get("User-Agent", "")[:255] if hasattr(request, "headers") else None
    )


def set_actor(user: Any | None) -> None:
    """Lightweight variant used by tests and tasks where no request exists."""
    if user is not None and getattr(user, "is_authenticated", False):
        actor_id = getattr(user, "id", None)
        _local.actor_id = str(actor_id) if actor_id is not None else None
        _local.actor_role = getattr(user, "role", "") or ""
        _local.tenant_id = getattr(user, "tenant_id", None)
    else:
        _local.actor_id = None
        _local.actor_role = ""
        _local.tenant_id = None


def clear() -> None:
    for attr in ("actor_id", "actor_role", "tenant_id", "request_id", "ip_hash", "user_agent"):
        if hasattr(_local, attr):
            delattr(_local, attr)


def get_actor_id() -> str | None:
    return getattr(_local, "actor_id", None)


def get_actor_role() -> str:
    return getattr(_local, "actor_role", "") or ""


def get_tenant_id() -> Any | None:
    return getattr(_local, "tenant_id", None)


def get_request_id() -> str | None:
    return getattr(_local, "request_id", None)


def get_ip_hash() -> str | None:
    return getattr(_local, "ip_hash", None)


def get_user_agent() -> str | None:
    return getattr(_local, "user_agent", None)


def _client_ip(request: Any) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR") if hasattr(request, "META") else None
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") if hasattr(request, "META") else None


def _hash_ip(ip: str, tenant_id: Any = None) -> str:
    """Hash the IP with a project-wide salt + tenant binding (Story 1.13 §4.9).

    Binding `tenant_id` into the payload ensures identical IPs across tenants
    produce different hashes, preventing cross-tenant correlation while still
    letting forensic analysis match repeat-attackers within one tenant.
    """
    salt = getattr(settings, "AUDIT_IP_HASH_SALT", "path-advisor-local-audit-salt")
    payload = f"{tenant_id or ''}|{ip}".encode()
    return hashlib.sha256(salt.encode() + payload).hexdigest()
