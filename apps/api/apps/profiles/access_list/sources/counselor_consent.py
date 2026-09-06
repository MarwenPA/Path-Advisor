"""``CounselorConsentSource`` — Story 6.7/6.11.

Wraps `CounselorConsent` (Story 6.7) to expose granted, non-revoked
counselor access as `AccessListEntry` rows, including `last_accessed_at`
(Story 6.11) straight from the model field `touch_last_accessed` stamps.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, transaction
from django.utils import timezone

from apps.core.rls import bypass_rls
from apps.establishments.models import CounselorConsent, CounselorConsentStatus

from ..dto import AccessListEntry
from ..exceptions import EntryNotFound
from ..results import RevocationResult
from ..visibility_matrix import VISIBILITY_MATRIX

if TYPE_CHECKING:
    from apps.accounts.models import User


class CounselorConsentSource:
    """One source adapter — see ``AccessListSource`` protocol."""

    name = "counselor_consent"

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        # `bypass_rls` after `student=user` (the sole authorization source
        # here) — a student's RLS session can't see the counselor's `users`
        # row, which would silently zero out `select_related("counselor")`'s
        # JOIN on real Postgres (SQLite doesn't enforce RLS, so this only
        # surfaces there — same class of bug as Stories 5.6/5.7/5.9).
        with bypass_rls(reason="counselor_consent_source.list_for_user"):
            rows = list(
                CounselorConsent.objects.filter(
                    student=user,
                    status=CounselorConsentStatus.GRANTED,
                    revoked_at__isnull=True,
                ).select_related("counselor")
            )

        matrix = VISIBILITY_MATRIX["counselor"]
        entries: list[AccessListEntry] = []
        for row in rows:
            entries.append(
                AccessListEntry(
                    id=f"{self.name}:{row.id}",
                    tier_type="counselor",
                    display_name=row.counselor.email,
                    granted_at=row.decided_at or row.requested_at,
                    visible_data=matrix["visible"],
                    masked_data=matrix["masked"],
                    revocable=True,
                    source_name=self.name,
                    source_pk=str(row.id),
                    last_accessed_at=row.last_accessed_at,
                )
            )
        return entries

    def revoke(self, user: User, source_pk: str) -> RevocationResult:
        """Mirrors `ParentalConsentSource.revoke` (Story 1.10) — same
        select_for_update + ownership-assert + idempotent-already-revoked
        + malformed-pk-to-404 pattern."""
        try:
            with transaction.atomic():
                row = (
                    CounselorConsent.objects.select_for_update()
                    .filter(
                        student=user,
                        id=source_pk,
                        status=CounselorConsentStatus.GRANTED,
                    )
                    .first()
                )
                if row is None:
                    raise EntryNotFound(
                        f"CounselorConsent({source_pk}) not found for user {user.id}"
                    )
                if row.student_id != user.id:
                    raise EntryNotFound(f"CounselorConsent({source_pk}) ownership mismatch")
                if row.revoked_at is not None:
                    return RevocationResult.ALREADY_REVOKED

                row.revoked_at = timezone.now()
                row.save(update_fields=["revoked_at"])
                return RevocationResult.PERFORMED
        except (ValueError, ValidationError, DataError, IntegrityError) as exc:
            raise EntryNotFound(
                f"CounselorConsent({source_pk}) lookup invalid: {exc.__class__.__name__}"
            ) from exc

    def display_name_for(self, user: User, source_pk: str) -> str | None:
        try:
            with bypass_rls(reason="counselor_consent_source.display_name_for"):
                return (
                    CounselorConsent.objects.filter(student=user, id=source_pk)
                    .values_list("counselor__email", flat=True)
                    .first()
                )
        except (ValueError, ValidationError, DataError):
            return None
