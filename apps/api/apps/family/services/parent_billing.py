"""Parent-pays-premium-for-child — Story 6.4.

Every function here re-authorizes via `resolve_linked_child` (the sole
authorization source for any parent→child action, per `parent_view.py`'s
own invariant) before touching billing. Business logic itself (checkout
session creation, cancellation, tier state) is NOT duplicated — delegated
straight to `apps.billing.services`, passing the child as the explicit
`beneficiary`/`user` so the existing webhook/gating machinery (Story 5.1-5.3)
needs no special-casing for "who's paying".
"""

from __future__ import annotations

from typing import Any

from apps.accounts.models import User
from apps.billing.services.billing_service import BillingService
from apps.billing.services.provider import CheckoutSession
from apps.billing.services.subscription_service import SubscriptionService
from apps.family.services.parent_view import resolve_linked_child


def create_child_checkout_session(parent: User, student_id: str) -> CheckoutSession:
    """AC1/AC2 — parent-initiated Stripe Checkout, child is the beneficiary."""
    student = resolve_linked_child(parent, student_id)
    return BillingService().create_checkout_session(user=parent, beneficiary=student)


def get_child_subscription_status(parent: User, student_id: str) -> dict[str, Any]:
    """AC3 — "Mes abonnements": current tier/status + next billing date for
    the child. §2 scope decision: no Stripe invoice-history listing here —
    no such integration exists anywhere in this codebase yet (nothing lists
    past invoices even for a student's own subscription); building one would
    be new Stripe API surface, not a byproduct of "parent views status"."""
    student = resolve_linked_child(parent, student_id)
    sub = SubscriptionService.get_for_user(student)
    return {
        "tier": sub.tier if sub else "free",
        "status": sub.status if sub else "active",
        "current_period_end": sub.current_period_end if sub else None,
        "cancel_at_period_end": bool(sub and sub.cancel_at_period_end),
        "is_premium": bool(sub and sub.is_active_now),
        "paid_by_parent": bool(sub and sub.paid_by_id == parent.id),
    }


def cancel_child_subscription(parent: User, student_id: str):
    """AC3 — cancel at period end; impacts only the child, only once the
    already-paid period ends (`SubscriptionService.request_cancellation`'s
    existing behavior — nothing Story-6.4-specific to add there)."""
    student = resolve_linked_child(parent, student_id)
    return SubscriptionService.request_cancellation(user=student)
