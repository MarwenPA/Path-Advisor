"""Subscription lifecycle + gating service — Story 5.2.

All subscription state transitions driven by Stripe webhooks flow through
`apply_event`, which runs under `bypass_rls` (the webhook has no RLS identity)
and is audited. `is_premium` / `require_premium` are the gating entry points
used by permissions and premium-gated business services.
"""

from __future__ import annotations

from datetime import UTC, timedelta

import structlog
from django.utils import timezone

from apps.audit.decorators import audit_action
from apps.billing.models import Subscription
from apps.core.exceptions import InsufficientPlan
from apps.core.rls import bypass_rls

log = structlog.get_logger(__name__)

GRACE_DAYS = 7


class SubscriptionService:
    # --- gating -----------------------------------------------------------

    @staticmethod
    def get_for_user(user) -> Subscription | None:
        return Subscription.objects.filter(user=user).first()

    @classmethod
    def is_premium(cls, user) -> bool:
        sub = cls.get_for_user(user)
        return bool(sub and sub.is_active_now)

    @classmethod
    def require_premium(cls, user) -> None:
        """Raise `InsufficientPlan` (402 RFC 7807) if the user is not premium."""
        if not cls.is_premium(user):
            raise InsufficientPlan()

    # --- webhook-driven lifecycle ----------------------------------------

    @classmethod
    @audit_action("billing.subscription_event_applied")
    def apply_event(cls, *, event_type: str, obj: dict) -> bool:
        """Apply a Stripe subscription lifecycle event to local state.

        `obj` is the Stripe event's `data.object`. Runs as system actor
        (webhook has no session identity) → bypass_rls for the write.

        Returns True iff a handler existed for `event_type` (code-review fix,
        2026-08) — `BillingService.record_webhook_event` uses this to decide
        whether the event may be marked `processed_at` permanently, so an
        event type with no handler YET stays reprocessable once one lands.
        """
        handler = {
            "checkout.session.completed": cls._on_checkout_completed,
            "customer.subscription.updated": cls._on_subscription_updated,
            "customer.subscription.deleted": cls._on_subscription_deleted,
            "invoice.payment_failed": cls._on_payment_failed,
        }.get(event_type)
        if handler is None:
            return False
        with bypass_rls(reason=f"billing.webhook:{event_type}"):
            handler(obj)
        return True

    @staticmethod
    def _resolve_user(obj: dict):
        # Local import avoids an app-layering import cycle at module load.
        from apps.accounts.models import User

        user_id = obj.get("client_reference_id")
        if user_id:
            return User.objects.filter(id=user_id).first()
        return None

    @classmethod
    def _on_checkout_completed(cls, obj: dict) -> None:
        user = cls._resolve_user(obj)
        if user is None:
            log.warning("billing.checkout_completed_no_user", obj_id=obj.get("id"))
            return
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "tier": Subscription.Tier.PREMIUM,
                "status": Subscription.Status.ACTIVE,
                "grace_until": None,
                "stripe_customer_id": obj.get("customer", "") or "",
                "stripe_subscription_id": obj.get("subscription", "") or "",
                "current_period_end": _ts(obj.get("current_period_end")),
            },
        )

    @classmethod
    def _by_stripe_sub(cls, obj: dict) -> Subscription | None:
        sub_id = obj.get("id") or obj.get("subscription")
        if not sub_id:
            return None
        return Subscription.objects.filter(stripe_subscription_id=sub_id).first()

    @classmethod
    def _on_subscription_updated(cls, obj: dict) -> None:
        sub = cls._by_stripe_sub(obj)
        if sub is None:
            return
        stripe_status = obj.get("status")
        if stripe_status == "past_due":
            cls._mark_past_due(sub)
            return
        if stripe_status in ("active", "trialing"):
            sub.status = Subscription.Status.ACTIVE
            sub.tier = Subscription.Tier.PREMIUM
            sub.grace_until = None
        sub.current_period_end = _ts(obj.get("current_period_end")) or sub.current_period_end
        sub.save(
            update_fields=["status", "tier", "grace_until", "current_period_end", "updated_at"]
        )

    @classmethod
    def _on_subscription_deleted(cls, obj: dict) -> None:
        sub = cls._by_stripe_sub(obj)
        if sub is None:
            return
        sub.status = Subscription.Status.CANCELLED
        sub.tier = Subscription.Tier.FREE
        sub.grace_until = None
        sub.save(update_fields=["status", "tier", "grace_until", "updated_at"])

    @classmethod
    def _on_payment_failed(cls, obj: dict) -> None:
        sub = cls._by_stripe_sub(obj)
        if sub is None:
            return
        cls._mark_past_due(sub)

    @staticmethod
    def _mark_past_due(sub: Subscription) -> None:
        sub.status = Subscription.Status.PAST_DUE
        if sub.grace_until is None:
            sub.grace_until = timezone.now() + timedelta(days=GRACE_DAYS)
        sub.save(update_fields=["status", "grace_until", "updated_at"])

    # --- dunning (Celery beat) -------------------------------------------

    @classmethod
    def process_dunning(cls) -> int:
        """Send J+0/J+3/J+7 dunning emails and downgrade grace-expired subs.

        Returns the number of subscriptions downgraded. Idempotent enough to
        run daily (email send is a stub until Story 8.1).
        """
        now = timezone.now()
        downgraded = 0
        with bypass_rls(reason="billing.dunning"):
            past_due = Subscription.objects.filter(status=Subscription.Status.PAST_DUE)
            for sub in past_due.iterator():
                if sub.grace_until and sub.grace_until <= now:
                    sub.tier = Subscription.Tier.FREE
                    sub.status = Subscription.Status.CANCELLED
                    sub.grace_until = None
                    sub.save(update_fields=["tier", "status", "grace_until", "updated_at"])
                    _send_dunning_email(sub, day=GRACE_DAYS, final=True)
                    downgraded += 1
        return downgraded


def _ts(value) -> timezone.datetime | None:
    """Stripe sends unix seconds; convert to an aware datetime or None."""
    if not value:
        return None
    from datetime import datetime

    return datetime.fromtimestamp(int(value), tz=UTC)


def _send_dunning_email(sub: Subscription, *, day: int, final: bool = False) -> None:
    """Stub — real transactional email lands in Story 8.1. Patchable in tests."""
    log.info("billing.dunning_email", user_id=sub.user_id, day=day, final=final)
