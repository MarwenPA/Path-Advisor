"""Story 8.2 — preference management (auth) + tokenized unsubscribe (public).

The unsubscribe endpoint mirrors the parental-consent shape: anonymous,
token-authenticated, throttled, and writing through `bypass_rls` with a
named reason (a nominal call site per `core/rls.py`'s contract — the email
recipient clicking their own footer link has no session, yet must be able
to flip their own RLS-protected row).

POST, not GET, mutates: email-client link prefetchers follow GETs, and a
prefetcher must never unsubscribe anyone. The public frontend page does
the one-click confirm and POSTs.
"""

from __future__ import annotations

import structlog
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAuthenticatedAndActive
from apps.core.rls import bypass_rls
from apps.core.throttling import PublicSeoAnonThrottle

from .models import NotificationCategory, NotificationPreference
from .tokens import read_unsubscribe_token

log = structlog.get_logger(__name__)


class NotificationPreferencesView(APIView):
    """GET/PUT /api/v1/me/notification-preferences/ — the settings page API."""

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request: Request) -> Response:
        rows = {
            p.category: p.enabled
            # `user_id=...pk` rather than `user=request.user`: mypy types
            # request.user as User | AnonymousUser and refuses the union in
            # the lookup; after IsAuthenticatedAndActive it is a User, and
            # pk is typed on both.
            for p in NotificationPreference.objects.filter(user_id=request.user.pk)
        }
        return Response(
            {
                "preferences": [
                    {
                        "category": value,
                        "label": label,
                        # Opt-out model: no row means enabled.
                        "enabled": rows.get(value, True),
                    }
                    for value, label in NotificationCategory.choices
                ]
            }
        )

    def put(self, request: Request) -> Response:
        category = request.data.get("category")
        enabled = request.data.get("enabled")
        if category not in NotificationCategory.values or not isinstance(enabled, bool):
            return Response(
                {"detail": "category (connue) et enabled (booléen) sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        NotificationPreference.objects.update_or_create(
            user_id=request.user.pk, category=category, defaults={"enabled": enabled}
        )
        return Response({"category": category, "enabled": enabled})


class UnsubscribeView(APIView):
    """POST /api/v1/notifications/unsubscribe/ — the legal footer link's target."""

    permission_classes = [AllowAny]
    authentication_classes = []  # token IS the auth; no session/CSRF interplay
    throttle_classes = [PublicSeoAnonThrottle]

    def post(self, request: Request) -> Response:
        parsed = read_unsubscribe_token(str(request.data.get("token", "")))
        if parsed is None:
            return Response(
                {"detail": "Lien de désinscription invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_id, category = parsed
        # Anonymous click on an RLS-protected row: nominal bypass call site
        # (same pattern as parental-consent decide — the token proves the
        # actor's claim on exactly this row).
        with bypass_rls(reason="notifications.unsubscribe_via_signed_token"):
            NotificationPreference.objects.update_or_create(
                user_id=user_id, category=category, defaults={"enabled": False}
            )
        log.info("notifications.unsubscribed", category=category)
        return Response({"category": category, "label": NotificationCategory(category).label})


class DeltaRecapView(APIView):
    """Story 8.6 — GET /api/v1/me/delta-recap/ : the "what moved" cards.

    First call ever: creates the baseline cursor at `now` and returns zero
    cards (a fresh account has no "since your last visit"). Cursor younger
    than 24 h (UX-DR29's J+1 rule): zero cards. Otherwise: cards computed
    since the cursor — WITHOUT moving it. The cursor only moves on explicit
    ACK below; closing the tab re-proposes the same deltas next time.
    """

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request: Request) -> Response:
        from .delta_recap import RECAP_MIN_AGE, compute_cards, get_or_init_cursor

        cursor, created = get_or_init_cursor(request.user)
        if created or cursor.seen_at > timezone.now() - RECAP_MIN_AGE:
            return Response({"cards": []})
        cards = compute_cards(request.user, cursor.seen_at)
        return Response({"cards": cards})


class DeltaRecapAckView(APIView):
    """Story 8.6 — POST /api/v1/me/delta-recap/ack/ : « Tout vu, continuer ».

    Also fired by any card CTA click (navigating through a card = having
    seen the recap). Idempotent; always 204.
    """

    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request: Request) -> Response:
        from .delta_recap import acknowledge

        acknowledge(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
