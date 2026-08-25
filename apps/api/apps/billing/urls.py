"""URL patterns for billing — Story 5.1.

The webhook is wired directly in the root urlconf (outside /api/v1/), so this
module only exposes the authenticated /api/v1/billing/ surface.
"""

from django.urls import path

from apps.billing.views import CheckoutSessionView, SubscriptionStatusView

app_name = "billing"

urlpatterns = [
    path("checkout-session", CheckoutSessionView.as_view(), name="checkout-session"),
    path("subscription", SubscriptionStatusView.as_view(), name="subscription"),
]
