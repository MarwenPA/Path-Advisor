"""`TenantSessionMiddleware` — Story 1.8 T2.

Covers thread-local population (always-on) + the SQLite no-op path. The PG
GUC writes are exercised by `apps/accounts/tests/test_rls_isolation.py`
under the `make test-rls` job (Story 1.8 T4-T6), since they have no
observable effect on SQLite.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from apps.accounts.tests.factories import UserFactory
from apps.core import request_context
from path_advisor.middleware.tenant import TenantSessionMiddleware


def _make_request(user=None) -> object:
    request = RequestFactory().get("/api/v1/me/")
    request.user = user if user is not None else AnonymousUser()
    return request


@pytest.mark.django_db
def test_middleware_populates_thread_local_for_authenticated_user():
    user = UserFactory(tenant_id=uuid.uuid4(), role="counselor")
    captured = {}

    def view(_request):
        captured["actor_id"] = request_context.get_actor_id()
        captured["tenant_id"] = request_context.get_tenant_id()
        captured["actor_role"] = request_context.get_actor_role()
        response = MagicMock()
        response.status_code = 200
        return response

    middleware = TenantSessionMiddleware(view)
    middleware(_make_request(user=user))

    assert captured["actor_id"] == user.id
    assert captured["tenant_id"] == user.tenant_id
    assert captured["actor_role"] == "counselor"


@pytest.mark.django_db
def test_middleware_clears_thread_local_after_request():
    """A reused thread must not leak the previous request's actor."""
    user = UserFactory()

    def view(_request):
        # Mid-request the actor is set.
        assert request_context.get_actor_id() == user.id
        response = MagicMock()
        response.status_code = 200
        return response

    middleware = TenantSessionMiddleware(view)
    middleware(_make_request(user=user))
    # Post-response: thread-local is wiped.
    assert request_context.get_actor_id() is None
    assert request_context.get_tenant_id() is None
    assert request_context.get_actor_role() == ""


@pytest.mark.django_db
def test_middleware_clears_thread_local_even_when_view_raises():
    user = UserFactory()

    def view(_request):
        raise RuntimeError("simulated view crash")

    middleware = TenantSessionMiddleware(view)
    with pytest.raises(RuntimeError):
        middleware(_make_request(user=user))
    assert request_context.get_actor_id() is None


@pytest.mark.django_db
def test_middleware_handles_anonymous_user():
    captured = {}

    def view(_request):
        captured["actor_id"] = request_context.get_actor_id()
        captured["tenant_id"] = request_context.get_tenant_id()
        captured["actor_role"] = request_context.get_actor_role()
        response = MagicMock()
        response.status_code = 200
        return response

    middleware = TenantSessionMiddleware(view)
    middleware(_make_request())  # AnonymousUser

    # Audit thread-local is set to "nobody" — RLS GUCs default to empty,
    # which the policies treat as deny.
    assert captured["actor_id"] is None
    assert captured["tenant_id"] is None
    assert captured["actor_role"] == ""


@pytest.mark.django_db
def test_middleware_handles_b2c_user_with_null_tenant():
    """B2C accounts have `tenant_id = None`; middleware must not crash."""
    user = UserFactory(tenant_id=None)
    captured = {}

    def view(_request):
        captured["tenant_id"] = request_context.get_tenant_id()
        response = MagicMock()
        response.status_code = 200
        return response

    middleware = TenantSessionMiddleware(view)
    middleware(_make_request(user=user))
    assert captured["tenant_id"] is None
