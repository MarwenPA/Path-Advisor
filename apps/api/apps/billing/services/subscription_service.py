"""Subscription lifecycle + gating service — Story 5.2.

All subscription state transitions driven by Stripe webhooks flow through
`apply_event`, which runs under `bypass_rls` (the webhook has no RLS identity)
and is audited. `is_premium` / `require_premium` are the gating entry points
used by permissions and premium-gated business services.
"""

from __future__ import annotations

from datetime import UTC, timedelta

import structlog
from django.db import transaction
from django.utils import timezone

from apps.audit.decorators import audit_action, record_audit
from apps.audit.models import AuditResult
from apps.billing.exceptions import NoActiveSubscription
from apps.billing.models import Subscription
from apps.core.exceptions import InsufficientPlan
from apps.core.rls import bypass_rls

log = structlog.get_logger(__name__)

GRACE_DAYS = 7

# Stripe subscription statuses that keep the local row `active`/premium.
_LIVE_STATUSES = ("active", "trialing")
# Every other status (canceled, unpaid, incomplete_expired, paused, …) is
# treated as terminal (code review fix — a subscription must never stay
# premium/active locally once Stripe reports anything outside past_due/live).


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

    # --- user-initiated cancellation (Story 5.3 AC3) ----------------------

    @classmethod
    @audit_action(
        "billing.subscription_cancellation_requested",
        subject_from=lambda kwargs, ret: kwargs["user"].id,
    )
    def request_cancellation(cls, *, user) -> Subscription:
        """Schedule the user's subscription to cancel at period end.

        Distinct from the provider's immediate `cancel_subscription` (used by
        merge-on-second-checkout and the RGPD `pre_delete` signal) — this
        keeps premium access live until `current_period_end`; Stripe's
        `customer.subscription.deleted` (5.2) does the actual downgrade once
        the period ends. Idempotent: calling twice is a no-op the second time.
        """
        sub = cls.get_for_user(user)
        if sub is None or not sub.stripe_subscription_id or not sub.is_active_now:
            raise NoActiveSubscription()
        if not sub.cancel_at_period_end:
            from apps.billing.services import get_payment_provider

            get_payment_provider().schedule_cancellation(
                stripe_subscription_id=sub.stripe_subscription_id
            )
            sub.cancel_at_period_end = True
            sub.save(update_fields=["cancel_at_period_end", "updated_at"])
        return sub

    # --- webhook-driven lifecycle ----------------------------------------

    @classmethod
    @audit_action("billing.subscription_event_applied")
    def apply_event(cls, *, event_type: str, obj: dict) -> bool:
        """Apply a Stripe subscription lifecycle event to local state.

        `obj` is the Stripe event's `data.object`. Runs as system actor
        (webhook has no session identity) → bypass_rls for the write.

        Returns True iff the event was actually applied to a `Subscription`
        row — NOT merely "a handler function exists for this event type".
        `BillingService.record_webhook_event` uses this to decide whether the
        event may be marked `processed_at` permanently.

        Code review fix (2026-08, round 2): the first fix only distinguished
        "unknown event type" from "known type" — a known-type event whose
        target `Subscription` row doesn't exist YET (plausible: Stripe does
        not guarantee webhook delivery order, so `customer.subscription.updated`
        can race ahead of the `checkout.session.completed` that creates the
        row) was still marked `handled=True` and thus permanently
        `processed_at`, silently and irrecoverably dropping the transition.
        Each handler below now returns whether it found+mutated a row.
        """
        handler = {
            "checkout.session.completed": cls._on_checkout_completed,
            "customer.subscription.updated": cls._on_subscription_updated,
            "customer.subscription.deleted": cls._on_subscription_deleted,
            "invoice.payment_failed": cls._on_payment_failed,
        }.get(event_type)
        if handler is None:
            return False
        # `transaction.atomic()` here is nested (a savepoint) when called from
        # `BillingService.record_webhook_event`'s outer atomic block, and a
        # fresh transaction when called standalone (e.g. tests) — either way
        # `select_for_update()` in the handlers below is guaranteed a
        # transaction to run in (code review fix: lock the Subscription row
        # for the duration of the write to close the lost-update race between
        # different event types touching the same subscription).
        with transaction.atomic(), bypass_rls(reason=f"billing.webhook:{event_type}"):
            return bool(handler(obj))

    @staticmethod
    def _resolve_user(obj: dict):
        # Local import avoids an app-layering import cycle at module load.
        from apps.accounts.models import User

        user_id = obj.get("client_reference_id")
        if user_id:
            return User.objects.filter(id=user_id).first()
        return None

    @classmethod
    def _on_checkout_completed(cls, obj: dict) -> bool:
        user = cls._resolve_user(obj)
        if user is None:
            log.warning("billing.checkout_completed_no_user", obj_id=obj.get("id"))
            return False

        new_stripe_sub_id = obj.get("subscription", "") or ""
        # Lock any existing row for this user for the duration of the write —
        # closes the lost-update race between webhook events touching the
        # same subscription (code review fix: no lock existed previously).
        existing = Subscription.objects.select_for_update().filter(user=user).first()

        # Code review decision: "merge" a second checkout into a single live
        # Stripe subscription per user. If the user already has a *different*
        # stripe_subscription_id on file, the old one is superseded — cancel
        # it at Stripe (best-effort) so Path-Advisor never tracks/bills two
        # subscriptions for one user (previously a silent overwrite orphaned
        # the old one, a billing leak).
        if (
            existing
            and existing.stripe_subscription_id
            and existing.stripe_subscription_id != new_stripe_sub_id
        ):
            cls._cancel_superseded_subscription(existing.stripe_subscription_id)

        # Story 6.4 — a parent-paid checkout carries `paid_by_user_id` in
        # Stripe's `metadata` (set in `BillingService.create_checkout_session`
        # when `beneficiary` was passed). A plain self-checkout has no
        # metadata, so this is `None` and the field is cleared — correct:
        # a later self-renewal by the (now-adult?) student must not keep
        # showing "payé par ton parent" from a stale prior purchase.
        paid_by_user_id = (obj.get("metadata") or {}).get("paid_by_user_id") or None

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "tier": Subscription.Tier.PREMIUM,
                "status": Subscription.Status.ACTIVE,
                "grace_until": None,
                # A fresh activation clears any prior scheduled cancellation
                # (Story 5.3) — this IS the new subscription, not a
                # continuation of one the user had asked to end.
                "cancel_at_period_end": False,
                "stripe_customer_id": obj.get("customer", "") or "",
                "stripe_subscription_id": new_stripe_sub_id,
                "current_period_end": _ts(obj.get("current_period_end")),
                "paid_by_id": paid_by_user_id,
            },
        )
        if paid_by_user_id:
            # AC4 — a durable trace linking paying_user_id (parent) to
            # beneficiary_user_id (student), distinct from the generic
            # `billing.subscription_event_applied` wrapper on `apply_event`.
            record_audit(
                action="billing.premium_purchased_by_parent",
                result=AuditResult.SUCCESS,
                subject_id=user.id,
                metadata={"paying_user_id": paid_by_user_id, "beneficiary_user_id": user.id},
            )
        # Story 5.3 AC2 — best-effort confirmation email; must never fail the
        # webhook (record_webhook_event's transaction would roll back the
        # activation itself on any raise here).
        try:
            from apps.billing.services.emails import send_premium_activated

            send_premium_activated(user)
        except Exception as exc:
            log.warning("billing.premium_activated_email_failed", error=str(exc))
        return True

    @staticmethod
    def _cancel_superseded_subscription(stripe_subscription_id: str) -> None:
        """Best-effort cancel of a Stripe subscription superseded by a newer
        checkout for the same user (merge-on-second-checkout policy).

        Never raises — a failure here must not block activating the new
        subscription; it's logged for manual reconciliation in the Stripe
        dashboard if it ever happens.
        """
        from apps.billing.services import get_payment_provider

        try:
            get_payment_provider().cancel_subscription(
                stripe_subscription_id=stripe_subscription_id
            )
        except Exception as exc:
            log.error(
                "billing.supersede_cancel_failed",
                stripe_subscription_id=stripe_subscription_id,
                error=str(exc),
            )

    @classmethod
    def _by_stripe_sub(cls, obj: dict) -> Subscription | None:
        sub_id = obj.get("id") or obj.get("subscription")
        if not sub_id:
            return None
        return (
            Subscription.objects.select_for_update().filter(stripe_subscription_id=sub_id).first()
        )

    @classmethod
    def _on_subscription_updated(cls, obj: dict) -> bool:
        sub = cls._by_stripe_sub(obj)
        if sub is None:
            return False
        stripe_status = obj.get("status")
        if stripe_status == "past_due":
            cls._mark_past_due(sub)
            return True
        if stripe_status in _LIVE_STATUSES:
            sub.status = Subscription.Status.ACTIVE
            sub.tier = Subscription.Tier.PREMIUM
            sub.grace_until = None
        else:
            # Terminal/negative status (canceled, unpaid, incomplete_expired,
            # paused, …) — code review fix: previously fell through and left
            # status/tier stale, letting a subscription stay premium/active
            # forever after Stripe genuinely terminated billing.
            sub.status = Subscription.Status.CANCELLED
            sub.tier = Subscription.Tier.FREE
            sub.grace_until = None
        sub.current_period_end = _ts(obj.get("current_period_end")) or sub.current_period_end
        # Story 5.3 AC3 — Stripe is the source of truth for this flag; syncs
        # both directions (a user could also toggle it back off from the
        # Stripe customer portal, if that's ever exposed).
        if "cancel_at_period_end" in obj:
            sub.cancel_at_period_end = bool(obj.get("cancel_at_period_end"))
        sub.save(
            update_fields=[
                "status",
                "tier",
                "grace_until",
                "current_period_end",
                "cancel_at_period_end",
                "updated_at",
            ]
        )
        return True

    @classmethod
    def _on_subscription_deleted(cls, obj: dict) -> bool:
        sub = cls._by_stripe_sub(obj)
        if sub is None:
            return False
        sub.status = Subscription.Status.CANCELLED
        sub.tier = Subscription.Tier.FREE
        sub.grace_until = None
        sub.cancel_at_period_end = False
        sub.save(
            update_fields=["status", "tier", "grace_until", "cancel_at_period_end", "updated_at"]
        )
        return True

    @classmethod
    def _on_payment_failed(cls, obj: dict) -> bool:
        sub = cls._by_stripe_sub(obj)
        if sub is None:
            return False
        cls._mark_past_due(sub)
        return True

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
                if sub.grace_until is None:
                    # Self-heal (code review fix): a past_due row should never
                    # have a null grace_until in steady state — `_mark_past_due`
                    # always sets it — but a race could theoretically leave one
                    # null. Start the clock now rather than skip it forever.
                    sub.grace_until = now + timedelta(days=GRACE_DAYS)
                    sub.save(update_fields=["grace_until", "updated_at"])
                    continue
                if sub.grace_until <= now:
                    sub.tier = Subscription.Tier.FREE
                    sub.status = Subscription.Status.CANCELLED
                    sub.grace_until = None
                    sub.save(update_fields=["tier", "status", "grace_until", "updated_at"])
                    _send_dunning_email(sub, day=GRACE_DAYS, final=True)
                    downgraded += 1
        return downgraded


def _ts(value) -> timezone.datetime | None:
    """Stripe sends unix seconds; convert to an aware datetime or None.

    Guarded (code review fix) — a malformed/non-numeric value used to raise
    `int(value)` uncaught, poisoning the enclosing webhook `transaction.atomic()`
    block and causing Stripe to retry the exact same payload forever.
    """
    if not value:
        return None
    from datetime import datetime

    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OSError, OverflowError):
        log.warning("billing.invalid_timestamp", value=repr(value))
        return None


def _send_dunning_email(sub: Subscription, *, day: int, final: bool = False) -> None:
    """Stub — real transactional email lands in Story 8.1. Patchable in tests."""
    log.info("billing.dunning_email", user_id=sub.user_id, day=day, final=final)
