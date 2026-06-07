"""Custom login serializer — Story 1.12 (DELETED 403 leak) + Story 1.5 (status + lockout branches).

dj-rest-auth's default `LoginSerializer.validate()` calls `authenticate()` which
returns None for `is_active=False` users — translated to a generic 400/401 by
the upstream view. That's good baseline behaviour for the wrong-password path
(no enumeration leak), but it does not let the front-end disambiguate the
edge cases this serializer raises typed Problem Details for:

- `DELETED` → `AccountDeleted` (403) — Story 1.12
- `SUSPENDED` → `AccountSuspended` (403) — Story 1.5
- `EMAIL_UNVERIFIED` → `EmailNotVerified` (403 + resend hint) — Story 1.5
- per-account lockout → `AccountLocked` (400, generic body) — Story 1.5

PENDING_PARENTAL_CONSENT users log in normally (limited mode flag exposed via
`UserDetailsSerializer.is_fully_active`); ACTIVE users go through the
parent's `validate()` to `authenticate()`.

Failed-attempt counter (`apps.accounts.services.login_security`) is driven
from this serializer because we have the user resolved here and the post-
authenticate failure path is opaque from outside (DRF wraps the
ValidationError before the view sees it).

Wired in `settings.REST_AUTH['LOGIN_SERIALIZER']`.
"""

from __future__ import annotations

from typing import Any

from dj_rest_auth.serializers import LoginSerializer as _DjRestAuthLoginSerializer
from rest_framework.exceptions import ValidationError

from apps.accounts.gdpr_exceptions import (
    AccountDeleted,
    AccountLocked,
    AccountSuspended,
    EmailNotVerified,
)
from apps.accounts.models import UserStatus


class PathAdvisorLoginSerializer(_DjRestAuthLoginSerializer):
    """Reject status-blocked logins with typed Problem Details before delegating
    to dj-rest-auth's `authenticate()`. Drives the failed-attempt counter for
    wrong-password attempts on resolvable users.
    """

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Late imports — User model + service modules only available after Django
        # setup. Case-insensitive email lookup matches the Story 1.4 `email__iexact`
        # convention used elsewhere.
        from apps.accounts.models import User
        from apps.accounts.services import login_security

        email = attrs.get("email")
        candidate: User | None = None
        if email:
            candidate = (
                User.objects.filter(email__iexact=email)
                .only("id", "status", "locked_until")
                .first()
            )

        # Order matters: lockout is checked BEFORE status branches so a locked
        # user's password is never hashed against the stored hash (timing side-
        # channel hygiene). For non-existent emails the candidate is None and
        # we fall straight through to `super().validate()` — same enumeration
        # resistance as the parent class.
        if candidate is not None:
            if login_security.is_account_locked(candidate):
                # 400 + generic body — indistinguishable from "wrong password" so
                # an attacker can't detect that they just tripped the lockout
                # (cf. Story 1.5 §4.6 anti-pattern: do NOT use 423 Locked).
                raise AccountLocked()
            if candidate.status == UserStatus.DELETED:
                # 403 — Story 1.12 §AC3 deliberate UX leak for cancel-flow routing.
                raise AccountDeleted()
            if candidate.status == UserStatus.SUSPENDED:
                # 403 — Story 1.5 §AC3. Generic detail: do NOT reveal WHY.
                raise AccountSuspended()
            if candidate.status == UserStatus.EMAIL_UNVERIFIED:
                # 403 + resend hint in extras (Story 1.5 §AC3). `DomainError`
                # collects **kwargs into `self.extras` (NOT `extras={...}`,
                # which would nest it under a literal "extras" key).
                raise EmailNotVerified(
                    resend_endpoint="/api/v1/auth/registration/resend-email/",
                )

        # Delegate to dj-rest-auth's `authenticate()`. If the password is
        # wrong (or the email is unknown), the parent raises ValidationError.
        # We catch it, increment the per-account counter when the user exists,
        # then re-raise the SAME ValidationError so the response body shape
        # is identical regardless of which branch hit.
        try:
            attrs = super().validate(attrs)
        except ValidationError:
            if candidate is not None:
                # The view layer fills `ip_truncated` in the audit row it writes
                # on top of this serializer's failed-attempt accounting; the
                # service-layer call here gets None because we don't have the
                # request object at the serializer scope.
                login_security.record_failed_attempt(user=candidate)
            raise

        # NOTE — Story 1.6 semantic move: `clear_failed_attempts` USED to fire
        # here on password-only success (Story 1.5 §AC4). It now fires at the
        # view layer ONLY when the login is fully complete:
        #
        # - B2C non-MFA happy path → cleared in `ThrottledLoginView.post` right
        #   before posting the session cookie.
        # - MFA users (`user.requires_mfa=True`) → cleared in
        #   `mfa_challenge_view` / `mfa_enroll_confirm_view` on full success.
        #
        # Why: an attacker who guessed the password but can't pass MFA would
        # otherwise reset the per-account lockout on every guess, effectively
        # bypassing the 5-failures-in-15-min cap for the password leg.
        return attrs
