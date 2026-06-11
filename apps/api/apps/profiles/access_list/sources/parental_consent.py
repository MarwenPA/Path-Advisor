"""``ParentalConsentSource`` — the only AccessListSource live in Story 1.9.

Wraps the ``ParentalConsent`` model from Story 1.4 to expose granted, not-yet-
revoked parental access as ``AccessListEntry`` rows. The model has ``decision``,
``decided_at``, ``parent_email``, ``revoked_at`` (migration 0013), and
``revocation_notification_sent_at`` (migration 0014, Story 1.10 review D5).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import ParentalConsent, ParentalConsentDecision

from ..dto import AccessListEntry
from ..exceptions import EntryNotFound
from ..results import RevocationResult
from ..visibility_matrix import VISIBILITY_MATRIX

if TYPE_CHECKING:
    from apps.accounts.models import User

log = logging.getLogger(__name__)


class ParentalConsentSource:
    """One source adapter — see ``AccessListSource`` protocol."""

    name = "parental_consent"

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        # Story 1.10 review D1 — surface orphan granted rows with `decided_at IS
        # NULL` using `created_at` as a fallback (CNIL Article 15/17 anti-
        # "ghost access" guarantee). Log via Sentry so the orphan is investigated.
        rows = ParentalConsent.objects.filter(
            student=user,
            decision=ParentalConsentDecision.GRANTED,
            revoked_at__isnull=True,
        ).only("id", "parent_email", "decided_at", "created_at")

        matrix = VISIBILITY_MATRIX["parent"]
        entries: list[AccessListEntry] = []
        for row in rows:
            granted_at = row.decided_at
            if granted_at is None:
                granted_at = row.created_at
                log.warning(
                    "access_list.orphan_granted_consent",
                    extra={"consent_id": str(row.id), "user_id": user.id},
                )
            entries.append(
                AccessListEntry(
                    id=f"{self.name}:{row.id}",
                    tier_type="parent",
                    display_name=row.parent_email,
                    granted_at=granted_at,
                    visible_data=matrix["visible"],
                    masked_data=matrix["masked"],
                    revocable=True,
                    source_name=self.name,
                    source_pk=str(row.id),
                )
            )
        return entries

    def revoke(self, user: User, source_pk: str) -> RevocationResult:
        """Story 1.10 §AC4 + §T2, with review patches P2 P3 P4 P13 D5.

        Returns ``RevocationResult.PERFORMED`` on first revocation,
        ``ALREADY_REVOKED`` if the row was already revoked (idempotent — the
        revoker uses this to skip a second audit row, per AC9).

        Raises ``EntryNotFound`` if no granted, decision-set row matches
        ``(user, source_pk)`` — the view turns this into 404. Filter is
        deliberately strict (decision=GRANTED, decided_at__isnull=False) so a
        pending or refused consent cannot be "revoked" via guessed pk (review
        finding P3 — would otherwise stamp `revoked_at` + spam-email the parent).

        Translates `(ValueError, ValidationError, DataError)` from a malformed
        ``source_pk`` (review P13) into `EntryNotFound` so the view returns 404
        instead of 500.
        """
        try:
            with transaction.atomic():
                row = (
                    ParentalConsent.objects.select_for_update()
                    .filter(
                        student=user,
                        id=source_pk,
                        decision=ParentalConsentDecision.GRANTED,
                        decided_at__isnull=False,
                    )
                    .first()
                )
                if row is None:
                    raise EntryNotFound(
                        f"ParentalConsent({source_pk}) not found for user {user.id}"
                    )

                # P2 — defense-in-depth : explicit ownership assert after fetch,
                # even though the filter already includes `student=user`. Catches
                # a future bug where someone changes the filter without realizing
                # the security invariant.
                if row.student_id != user.id:
                    raise EntryNotFound(f"ParentalConsent({source_pk}) ownership mismatch")

                if row.revoked_at is not None:
                    # P4 — signal idempotent success to revoker so it can skip
                    # writing a second `profile.access_revoked` audit row (AC9).
                    return RevocationResult.ALREADY_REVOKED

                row.revoked_at = timezone.now()
                row.save(update_fields=["revoked_at", "updated_at"])

                # D5 — dispatch via on_commit so the task only fires if the
                # transaction actually commits. Eliminates the silent-loss
                # window between commit and `.delay()` call. The task itself
                # is idempotent (checks `revocation_notification_sent_at`).
                transaction.on_commit(lambda: _enqueue_notify_task(str(row.id)))
                return RevocationResult.PERFORMED
        except (ValueError, ValidationError, DataError, IntegrityError) as exc:
            # P13 — malformed source_pk (non-UUID, too long, escape chars) :
            # translate to 404 instead of bubbling 500.
            raise EntryNotFound(
                f"ParentalConsent({source_pk}) lookup invalid: {exc.__class__.__name__}"
            ) from exc

    def display_name_for(self, user: User, source_pk: str) -> str | None:
        """Review P10 — return the parent's email so `revoke_entry` can write it
        into the audit metadata. Best-effort : returns None on miss.
        """
        try:
            return (
                ParentalConsent.objects.filter(student=user, id=source_pk)
                .values_list("parent_email", flat=True)
                .first()
            )
        except (ValueError, ValidationError, DataError):
            return None


def _enqueue_notify_task(consent_id: str) -> None:
    """Lazy import to avoid the Django app-loading cycle (task module imports models)."""
    from apps.accounts.tasks import notify_parental_consent_revoked

    notify_parental_consent_revoked.delay(consent_id)
