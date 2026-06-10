"""Actor-context middleware — Story 1.7 §T13.

Calls `apps.core.request_context.set_actor_from_request` at the start of
every request and clears it in `process_response`. The thread-local is
consumed by `@audit_action` decorators that have no request in their
signature.

Story 1.13 §T5.7 originally added manual calls inside the audit views as
a defense (`apps/audit/views.py:53,191`). This middleware makes those
calls redundant — but the audit-view wrappers stay in place as a
belt-and-braces safeguard.

**Placement (cf. `path_advisor/settings/base.py::MIDDLEWARE`):** MUST be
AFTER `django.contrib.auth.middleware.AuthenticationMiddleware` (so
`request.user` is resolved) and AFTER `django_otp.middleware.OTPMiddleware`
(so `request.user.is_verified()` is set by the time we capture context).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from apps.core import request_context


class ActorContextMiddleware:
    """Bind `request.user` to a thread-local on each request, clear on response."""

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        request_context.set_actor_from_request(request)
        try:
            response = self.get_response(request)
        finally:
            request_context.clear()
        return response
