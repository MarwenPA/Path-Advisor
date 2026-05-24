"""Custom login serializer — surfaces DELETED accounts as a typed 403 (Story 1.12).

dj-rest-auth's default `LoginSerializer.validate()` calls `authenticate()` which
returns None for `is_active=False` users — translated to a generic 400/401 by
the upstream view. That's good baseline behaviour (no enumeration leak), but
it does not let the front-end route a deleted-account login attempt to the
cancel-flow info page (story §AC3).

We deliberately opt INTO leaking the DELETED state at login time: the UX
benefit (user understands their account is in the 30-day grace window and
can click the cancel link in their email) outweighs the marginal enumeration
leak. The same email at the password reset endpoint is still rate-limited
and produces a generic Problem, so the leak is scoped to the login endpoint.

Wired in `settings.REST_AUTH['LOGIN_SERIALIZER']`.
"""

from __future__ import annotations

from typing import Any

from dj_rest_auth.serializers import LoginSerializer as _DjRestAuthLoginSerializer

from apps.accounts.gdpr_exceptions import AccountDeleted
from apps.accounts.models import UserStatus


class PathAdvisorLoginSerializer(_DjRestAuthLoginSerializer):
    """Reject DELETED-status logins with a typed 403 before delegating to auth."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        if email:
            # Late import — User model only available after Django setup. Case-insensitive
            # lookup matches the Story 1.4 `email__iexact` convention used elsewhere.
            from apps.accounts.models import User

            candidate = User.objects.filter(email__iexact=email).only("status").first()
            if candidate is not None and candidate.status == UserStatus.DELETED:
                # 403 with the AccountDeleted Problem Details — the front-end picks
                # this up by `type` URI and redirects to /auth/account-deleted (the
                # static post-soft-delete info page) with a hint about the cancel
                # link in the user's inbox.
                raise AccountDeleted()

        # Standard path — wrong creds / unknown email / inactive (non-DELETED) all
        # surface as the generic ValidationError dj-rest-auth raises. No leak.
        return super().validate(attrs)
