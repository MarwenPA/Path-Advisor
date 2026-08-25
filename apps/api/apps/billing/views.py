"""Billing API views — Story 5.1.

Two surfaces:
  POST /api/v1/billing/checkout-session  — auth + fully-active, returns hosted
      Stripe Checkout URL. Business logic delegated to BillingService.
  POST /webhooks/stripe/                 — Stripe → Django (single source of
      truth). CSRF-exempt, AllowAny (auth is the HMAC signature), idempotent.

No card data is ever handled here (PCI SAQ-A): checkout is hosted by Stripe and
the webhook only receives Stripe object ids.
"""

from __future__ import annotations

from typing import ClassVar

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.billing.services.billing_service import BillingService, InvalidWebhookSignature
from apps.core.permissions import IsAuthenticatedAndActive


class CheckoutSessionView(APIView):
    """POST /api/v1/billing/checkout-session — create a hosted Checkout session."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive]

    def post(self, request: Request) -> Response:
        # Provider failures surface as PaymentProviderError (RFC 7807) via the
        # global exception handler — never a bare 500.
        session = BillingService().create_checkout_session(user=request.user)
        return Response({"checkout_url": session.checkout_url}, status=status.HTTP_201_CREATED)


class SubscriptionStatusView(APIView):
    """GET /api/v1/billing/subscription — current tier/status for the user (Story 5.2)."""

    permission_classes: ClassVar = [IsAuthenticatedAndActive]

    def get(self, request: Request) -> Response:
        from apps.billing.services.subscription_service import SubscriptionService

        sub = SubscriptionService.get_for_user(request.user)
        return Response(
            {
                "tier": sub.tier if sub else "free",
                "status": sub.status if sub else "active",
                "current_period_end": sub.current_period_end if sub else None,
                "is_premium": bool(sub and sub.is_active_now),
            }
        )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook_view(request: Request) -> Response:
    """POST /webhooks/stripe/ — verify HMAC signature and record the event."""
    signature_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        BillingService().record_webhook_event(
            payload=request.body,
            signature_header=signature_header,
        )
    except InvalidWebhookSignature:
        # Code-review fix (2026-08): the HMAC signature IS this endpoint's
        # sole authentication proof — an invalid one is an auth failure and
        # must be audited like `auth.login_failed`, else a forged/replayed
        # webhook attempt leaves no trace for the DPO/security team.
        record_audit(
            action="billing.webhook_signature_invalid",
            result=AuditResult.FAILURE,
            metadata={"signature_header_present": bool(signature_header)},
        )
        return Response({"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)
