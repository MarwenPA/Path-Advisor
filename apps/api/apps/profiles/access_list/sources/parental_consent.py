"""``ParentalConsentSource`` — the only AccessListSource live in Story 1.9.

Wraps the ``ParentalConsent`` model from Story 1.4 to expose granted, not-yet-
revoked parental access as ``AccessListEntry`` rows. The model already has
``decision``, ``decided_at`` and ``parent_email`` ; Story 1.9 adds
``revoked_at`` via migration ``0013_parental_consent_revoked_at``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.accounts.models import ParentalConsent, ParentalConsentDecision

from ..dto import AccessListEntry
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
        """Story 1.10 implements this. Refusing to act in 1.9 is intentional."""
        raise NotImplementedError("ParentalConsentSource.revoke is implemented by Story 1.10.")
