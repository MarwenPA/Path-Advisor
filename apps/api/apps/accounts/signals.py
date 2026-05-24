"""Signal handlers — wire allauth lifecycle events into Path-Advisor services."""

from __future__ import annotations

from allauth.account.signals import email_confirmed, user_signed_up
from django.db import transaction
from django.dispatch import receiver

from apps.accounts.models import UserStatus
from apps.accounts.services.auth_service import mark_email_verified, record_signup_event
from apps.accounts.services.parental_consent import create_parental_consent_request
from apps.accounts.services.parental_consent_email import send_request_to_parent
from apps.core.rls import bypass_rls


@receiver(user_signed_up)
def _on_user_signed_up(sender, request, user, **kwargs) -> None:
    """Persist the signup event in the audit log + emit operational structlog.

    For minor accounts (status set to `pending_parental_consent` by the adapter), we
    additionally create a `ParentalConsent` row and dispatch the parent email. The
    child's email-confirmation flow runs in parallel — both must complete for the
    user to reach `is_fully_active = true` (cf. Story 1.4 §AC3 state machine).
    """
    record_signup_event(user=user)

    if user.status == UserStatus.PENDING_PARENTAL_CONSENT:
        # Allauth fires this with a plain WSGIRequest (no `.data`); the adapter stashes
        # the parent_email on the user object as a transient attribute. Reading from
        # `request.body` would force a second JSON parse and assume Content-Type.
        parent_email = getattr(user, "_parent_email_pending", None)
        if not parent_email:
            # Defense in depth: the serializer's cross-field validator already rejects
            # this combination, so reaching here implies an internal contract drift.
            # Log + skip rather than 500 — the User row is committed by allauth's
            # default `save_user`, so partial-failure recovery is the responsibility
            # of an operator who can read the structlog.
            return
        ip = _client_ip(request)
        user_agent = request.headers.get("user-agent", "") if request is not None else None
        # Story 1.4 review §P8: wrap consent creation in an explicit atomic block.
        # The User row is already committed (allauth's `save_user` ran before this
        # signal); the consent insert is the only DB write here, but using a clean
        # transaction boundary keeps the @audit_action row aligned with the consent
        # row if either fails.
        # `bypass_rls` (Story 1.8 D3): the signup signal runs anonymously,
        # so the `users` + `parental_consents` modify policies would deny
        # the consent row INSERT. The `ParentalConsent.save()` override
        # also reads the student's `tenant_id` from `users`, which is RLS-
        # protected. Audited via `rls.bypass_used` so every entry is grepable.
        with (
            transaction.atomic(),
            bypass_rls(
                reason="parental_consent.signup_signal",
                metadata={"student_id": user.id},
            ),
        ):
            consent = create_parental_consent_request(
                student=user,
                parent_email=parent_email,
                ip=ip,
                user_agent=user_agent,
            )
        # Dispatch outside the atomic block so an SMTP failure does not roll back the
        # consent row (the student can resend via /resend/, which auto-skips expired
        # consents per §P5). Returns a bool but we don't act on it here — the consent
        # exists, and tooling can replay reminders later.
        send_request_to_parent(consent)


@receiver(email_confirmed)
def _on_email_confirmed(sender, request, email_address, **kwargs) -> None:
    """Activate the user when they click the email-confirmation link.

    For minor accounts in `pending_parental_consent`, this transitions the user out of
    `email_unverified` semantically but the `status` field is only flipped to ACTIVE
    by `parental_consent.record_decision` once the parent grants — handled there to
    keep the state-machine logic in a single place (cf. Story 1.4 §AC3).
    """
    mark_email_verified(email_address.user)


def _client_ip(request) -> str | None:
    """Best-effort client IP — production gateways forward via X-Forwarded-For."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry is the original client; subsequent are proxies. Trust handled at
        # gateway level (Story 1.3 deferred work — RATELIMIT_TRUSTED_PROXIES).
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
