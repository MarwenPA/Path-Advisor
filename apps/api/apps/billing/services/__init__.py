"""Billing services package.

`get_payment_provider()` is the single selection point for the payment backend
(NFR-I1): callers never instantiate a concrete provider directly, so swapping
implementations is a one-line change here — everything else depends only on the
`PaymentProvider` interface.
"""

from __future__ import annotations

from apps.billing.services.provider import PaymentProvider


def get_payment_provider() -> PaymentProvider:
    """Return the configured payment provider instance."""
    # Local import keeps the stripe SDK out of the import path for callers that
    # only need the interface (and keeps this module import-cycle-free).
    from apps.billing.services.stripe_provider import StripeProvider

    return StripeProvider()


__all__ = ["PaymentProvider", "get_payment_provider"]
