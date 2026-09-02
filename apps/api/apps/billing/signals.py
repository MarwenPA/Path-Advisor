"""Billing signals — Story 5.2 (carried dependency from deferred-work.md).

When a User is hard-deleted, any active Stripe subscription must be cancelled
at the provider — the DB cascade cannot reach Stripe (it lives outside the DB).
Failure to cancel must NOT block account deletion (RGPD erasure takes priority);
we log + Sentry-capture and move on.
"""

from __future__ import annotations

import structlog
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver

log = structlog.get_logger(__name__)


@receiver(
    pre_delete, sender=settings.AUTH_USER_MODEL, dispatch_uid="billing_cancel_stripe_on_delete"
)
def cancel_stripe_subscription_on_user_delete(sender, instance, **kwargs) -> None:
    # Code review fix: the whole body is now inside one try/except — the
    # original code left the initial `Subscription` lookup outside the guard,
    # so a DB-level failure there (not just a Stripe API failure) would
    # propagate out of this `pre_delete` signal and abort the RGPD hard-delete
    # transaction, contradicting this module's own stated contract.
    try:
        from apps.billing.models import Subscription
        from apps.billing.services import get_payment_provider

        sub = Subscription.objects.filter(user=instance).first()
        if not sub or not sub.stripe_subscription_id:
            return
        get_payment_provider().cancel_subscription(
            stripe_subscription_id=sub.stripe_subscription_id
        )
    except Exception as exc:
        log.error(
            "billing.cancel_on_delete_failed",
            user_id=instance.id,
            error=str(exc),
        )
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
