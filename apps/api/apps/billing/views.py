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
        return Response({"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)
