"""``ParentLinkSource`` — Story 6.1 §T5, the `AccessListSource` adapter for
`ParentStudentLink`.

Mirrors `apps.profiles.access_list.sources.parental_consent.ParentalConsentSource`
structurally (ownership check, idempotent revoke, `VISIBILITY_MATRIX["parent"]`
reuse) but reads from the Story 6.1 model instead of `ParentalConsent`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, transaction
from django.utils import timezone

from apps.core.rls import bypass_rls
from apps.family.models import ParentStudentLink
from apps.profiles.access_list.dto import AccessListEntry
from apps.profiles.access_list.exceptions import EntryNotFound
from apps.profiles.access_list.results import RevocationResult
from apps.profiles.access_list.visibility_matrix import VISIBILITY_MATRIX

if TYPE_CHECKING:
    from apps.accounts.models import User

log = logging.getLogger(__name__)


class ParentLinkSource:
    """One source adapter — see ``AccessListSource`` protocol (Story 1.9)."""

    name = "parent_link"

    def list_for_user(self, user: User) -> list[AccessListEntry]:
        # The parent's `users` row is invisible to the student's own RLS session
        # (Story 1.8 `users_isolation_select` only exposes `id = current_user_id`
        # or same-tenant rows — a B2C parent is neither). The display name IS the
        # parent's own email, shown to the student who invited them, so the
        # cross-row read is legitimate — same rationale as
        # `apps.accounts.views.parental_consent_status` (Story 1.8 D3).
        with bypass_rls(reason="parent_link.list_display_names"):
            rows = list(
                ParentStudentLink.objects.filter(
                    student=user,
                    revoked_at__isnull=True,
                )
                .select_related("parent")
                .only("id", "parent__email", "linked_at")
            )

        matrix = VISIBILITY_MATRIX["parent"]
        entries: list[AccessListEntry] = []
        for row in rows:
            entries.append(
                AccessListEntry(
                    id=f"{self.name}:{row.id}",
                    tier_type="parent",
                    display_name=row.parent.email,
                    granted_at=row.linked_at,
                    visible_data=matrix["visible"],
                    masked_data=matrix["masked"],
                    revocable=True,
                    source_name=self.name,
                    source_pk=str(row.id),
                )
            )
        return entries

    def revoke(self, user: User, source_pk: str) -> RevocationResult:
        """AC5 / §T5.2 — stamps `revoked_at`, sends the parent notification,
        idempotent on a second call (§4.4 anti-pattern: no double-audit).

        Ownership check is explicit (`row.student_id == user.id`) in addition
        to the query filter — cf. story §4.4 / Story 1.9 review P2.
        """
        try:
            with transaction.atomic():
                row = (
                    ParentStudentLink.objects.select_for_update()
                    .filter(student=user, id=source_pk)
                    .first()
                )
                if row is None:
                    raise EntryNotFound(
                        f"ParentStudentLink({source_pk}) not found for user {user.id}"
                    )
                if row.student_id != user.id:
                    raise EntryNotFound(f"ParentStudentLink({source_pk}) ownership mismatch")
                if row.revoked_at is not None:
                    return RevocationResult.ALREADY_REVOKED

                row.revoked_at = timezone.now()
                row.save(update_fields=["revoked_at", "updated_at"])

                transaction.on_commit(lambda: _notify_parent_revoked(str(row.id)))
                return RevocationResult.PERFORMED
        except (ValueError, ValidationError, DataError, IntegrityError) as exc:
            raise EntryNotFound(
                f"ParentStudentLink({source_pk}) lookup invalid: {exc.__class__.__name__}"
            ) from exc

    def display_name_for(self, user: User, source_pk: str) -> str | None:
        try:
            # See `list_for_user` — the parent's email lives behind RLS on
            # `users`; open the audited bypass for this display-name read.
            with bypass_rls(reason="parent_link.display_name"):
                return (
                    ParentStudentLink.objects.filter(student=user, id=source_pk)
                    .select_related("parent")
                    .values_list("parent__email", flat=True)
                    .first()
                )
        except (ValueError, ValidationError, DataError):
            return None


def _notify_parent_revoked(link_id: str) -> None:
    """Lazy import to avoid the Django app-loading cycle (tasks import models)."""
    from apps.family.tasks import send_parent_link_revoked_email

    send_parent_link_revoked_email.delay(link_id)
