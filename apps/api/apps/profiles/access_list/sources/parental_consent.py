"""``ParentalConsentSource`` — the only AccessListSource live in Story 1.9.

Wraps the ``ParentalConsent`` model from Story 1.4 to expose granted, not-yet-
revoked parental access as ``AccessListEntry`` rows. The model already has
``decision``, ``decided_at`` and ``parent_email`` ; Story 1.9 adds
``revoked_at`` via migration ``0013_parental_consent_revoked_at``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import ParentalConsent, ParentalConsentDecision

from ..dto import AccessListEntry
from ..exceptions import EntryNotFound
from ..visibility_matrix import VISIBILITY_MATRIX

if TYPE_CHECKING:
    from apps.accounts.models import User


class ParentalConsentSource:
    """One source adapter — see ``AccessListSource`` protocol."""

    name = "parental_consent"

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        rows = ParentalConsent.objects.filter(
            student=user,
            decision=ParentalConsentDecision.GRANTED,
            revoked_at__isnull=True,
            decided_at__isnull=False,
        ).only("id", "parent_email", "decided_at")

        matrix = VISIBILITY_MATRIX["parent"]
        return [
            AccessListEntry(
                id=f"{self.name}:{row.id}",
                tier_type="parent",
                display_name=row.parent_email,
                granted_at=row.decided_at,
                visible_data=matrix["visible"],
                masked_data=matrix["masked"],
                revocable=True,
                source_name=self.name,
                source_pk=str(row.id),
            )
            for row in rows
        ]

    def revoke(self, user: User, source_pk: str) -> None:
        """Story 1.10 §AC4 + §T2 — set ``revoked_at = now()`` and dispatch the
        parent-notification Celery task.

        Idempotent : a second invocation on an already-revoked row is a no-op
        (no second update, no second email — the task itself checks
        ``notification_sent_at IS NULL`` before sending).

        Raises ``EntryNotFound`` if no row matches ``(user, source_pk)``
        regardless of revocation state — the view turns this into a 404.
        ``select_for_update`` serializes against the rare double-POST race.
        """
        with transaction.atomic():
            row = (
                ParentalConsent.objects.select_for_update()
                .filter(student=user, id=source_pk)
                .first()
            )
            if row is None:
                raise EntryNotFound(f"ParentalConsent({source_pk}) not found for user {user.id}")
            if row.revoked_at is not None:
                # Already revoked → idempotent success, no second side effect.
                return
            row.revoked_at = timezone.now()
            row.save(update_fields=["revoked_at", "updated_at"])

        # Dispatch the notification task OUTSIDE the transaction so a
        # transient broker hiccup does not rollback the revocation write.
        from apps.accounts.tasks import notify_parental_consent_revoked

        notify_parental_consent_revoked.delay(str(row.id))
