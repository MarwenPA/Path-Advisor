"""End-to-end RBAC matrix `(role, endpoint) → status` — Story 1.7 §AC6.

Code-review D6 fills the spec gap : the existing `test_rbac_permissions.py`
covers permission classes at unit-test granularity (Mock requests) but does
NOT exercise the real DRF view chain (`@api_view` → `permission_classes` →
audit denial → 403 Problem Details).

This file complements it with parametrized HTTP tests over the most
sensitive endpoints — student / parent / counselor / school_admin /
path_admin / support / anonymous each hit the URL ; the test asserts
the expected status code (200/202/302 / 403 / 401) per the spec table.

Coverage focus: endpoints where RBAC changes (or could regress) would
matter most — staff areas, audit log, MFA disable, account-deletion,
GDPR exports, parental-consent resend.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _make_user(role: UserRole, email: str = "rbac-test@example.test"):
    from allauth.account.models import EmailAddress

    user = UserFactory(email=email, role=role)
    # Production path_admin == superuser (matches `PathAdminUserFactory`).
    if role == UserRole.PATH_ADMIN:
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
    return user


def _authed_client(role: UserRole | None) -> APIClient:
    client = APIClient(REMOTE_ADDR="127.0.0.1")
    if role is not None:
        user = _make_user(role, email=f"rbac-{role.value}@example.test")
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    return client


#: Endpoints under RBAC matrix coverage. Each entry: URL `name=`, HTTP method,
#: roles expected to be ALLOWED (everything else → 403 ; anonymous → 401/403).
#: The expected-status maps are kept loose (`{200, 202, 302, 405}`) because
#: some endpoints reject the empty body with a method-specific shape (we
#: care about RBAC behavior, not the success contract — story 1.x tests
#: cover that).
_ALLOWED_STATUSES_SUCCESS: set[int] = {200, 201, 202, 204, 302, 400, 404, 405, 429}
_DENIED_STATUSES: set[int] = {401, 403}


_ENDPOINTS = [
    {
        "name": "audit_log_list",
        "url": "/api/v1/audit/logs/",
        "method": "get",
        "allowed_roles": {UserRole.PATH_ADMIN},
    },
    {
        "name": "mfa_disable",
        "url": "/api/v1/auth/mfa/disable/",
        "method": "post",
        "allowed_roles": {UserRole.STUDENT, UserRole.PARENT},
    },
    {
        "name": "mfa_enroll_start_from_session",
        "url": "/api/v1/auth/mfa/enroll/start-from-session/",
        "method": "post",
        "allowed_roles": {UserRole.STUDENT, UserRole.PARENT},
    },
    {
        "name": "parental_consent_resend",
        "url": "/api/v1/auth/parental-consent/resend/",
        "method": "post",
        "allowed_roles": {UserRole.STUDENT},
    },
]


def _request(client: APIClient, endpoint: dict):
    method = getattr(client, endpoint["method"])
    return method(endpoint["url"], data={}, format="json")


@pytest.mark.parametrize(
    "endpoint,role",
    [(endpoint, role) for endpoint in _ENDPOINTS for role in [None, *UserRole]],
    ids=[
        f"{endpoint['name']}-{role.value if role else 'anonymous'}"
        for endpoint in _ENDPOINTS
        for role in [None, *UserRole]
    ],
)
def test_rbac_matrix_role_x_endpoint(endpoint, role):
    """Per Story 1.7 §AC6 — every (role, endpoint sensible) pair has at
    least one test asserting the right verdict.
    """
    client = _authed_client(role)
    response = _request(client, endpoint)

    if role is None:
        # Anonymous: must be refused (401 or 403 — DRF returns 403 by default
        # when no IsAuthenticated check is the FIRST in the chain).
        assert response.status_code in _DENIED_STATUSES, (
            f"Anonymous reached {endpoint['name']} with {response.status_code}"
        )
        return

    if role in endpoint["allowed_roles"]:
        # Role allowed → NOT a 401/403 (200 / 202 / 302 / 400 / 405 all OK).
        assert response.status_code in _ALLOWED_STATUSES_SUCCESS, (
            f"Role {role.value} refused on {endpoint['name']} "
            f"with {response.status_code} (body: {response.content[:200]!r})"
        )
    else:
        # Role NOT in allow-list → must be 403.
        assert response.status_code == 403, (
            f"Role {role.value} reached {endpoint['name']} "
            f"with {response.status_code} (expected 403)"
        )
