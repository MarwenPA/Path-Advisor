"""AuditLog — append-only journal of access to a student's personal data.

Three layers of immutability:
1. PostgreSQL trigger (migration 0002) — refuses UPDATE/DELETE at the DB level.
2. ORM manager / queryset override — refuses .update()/.delete() / re-save.
3. SHA-256 hash chain — tampering detected by `verify_chain_integrity` task.

Write path: `apps.audit.decorators.audit_action()` or `record_audit()`. Reads are
restricted to `path_admin` users via `/api/v1/audit/logs/`.

See Story 1.13 §4.4 for the model design rationale.
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.db import models

from apps.core.exceptions import AuditLogImmutable
from apps.core.ids import generate_id


def _default_audit_id() -> str:
    return generate_id("aud")


class AuditResult(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"
    DENIED = "denied", "Denied"


class AuditLogQuerySet(models.QuerySet):
    """Refuse mutations at the ORM level — defense in depth on top of the PG trigger."""

    def update(self, **kwargs: Any) -> int:
        raise AuditLogImmutable(detail="audit_logs is append-only — update() is forbidden.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise AuditLogImmutable(detail="audit_logs is append-only — delete() is forbidden.")


class AuditLogManager(models.Manager.from_queryset(AuditLogQuerySet)):  # type: ignore[misc]
    """Bulk creation passes through; update/delete blocked above."""


class AuditLog(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_audit_id,
        editable=False,
    )

    # Actor + tenant snapshot — frozen at write time so audit survives downstream deletes.
    actor_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    actor_role = models.CharField(max_length=20, default="", db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Subject = the student whose data is touched (null for non-subject events like login_failed).
    subject_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    # `<domain>.<action>` — see docs/patterns/audit-events.md for the canonical catalog.
    action = models.CharField(max_length=100, db_index=True)
    result = models.CharField(
        max_length=20,
        choices=AuditResult.choices,
        default=AuditResult.SUCCESS,
        db_index=True,
    )

    request_id = models.CharField(max_length=32, null=True, blank=True)
    ip_address_hash = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    metadata = models.JSONField(default=dict)

    # SHA-256 chain — `prev_hash` references the previous row's `row_hash`. First row's prev is "".
    prev_hash = models.CharField(max_length=64, null=True, blank=True)
    row_hash = models.CharField(max_length=64)

    created_at = models.DateTimeField(db_index=True)

    objects = AuditLogManager()

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["subject_id", "-created_at"], name="idx_audit_subject_created"),
            models.Index(fields=["actor_id", "-created_at"], name="idx_audit_actor_created"),
            models.Index(fields=["action", "-created_at"], name="idx_audit_action_created"),
            models.Index(fields=["tenant_id", "-created_at"], name="idx_audit_tenant_created"),
            models.Index(fields=["result", "-created_at"], name="idx_audit_result_created"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"AuditLog({self.action} by {self.actor_id or 'anonymous'} "
            f"@ {self.created_at:%Y-%m-%dT%H:%M:%SZ})"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Refuse re-save on existing PK — the PG trigger blocks it at the DB level too,
        # but catching it here gives us a domain-typed exception instead of a raw IntegrityError.
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise AuditLogImmutable(detail="audit_logs row already persisted; rewrite forbidden.")
        super().save(*args, **kwargs)
