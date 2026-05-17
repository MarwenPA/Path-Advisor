"""Read-only Django admin for `AuditLog` — DPOs browse the journal here in MVP."""

from typing import ClassVar

from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display: ClassVar[tuple] = ("created_at", "actor_id", "actor_role", "action", "subject_id", "result")
    list_filter: ClassVar[tuple] = ("result", "actor_role", "action")
    search_fields: ClassVar[tuple] = ("actor_id", "subject_id", "action", "request_id")
    readonly_fields: ClassVar[tuple] = (
        "id",
        "created_at",
        "actor_id",
        "actor_role",
        "tenant_id",
        "subject_id",
        "action",
        "result",
        "request_id",
        "ip_address_hash",
        "user_agent",
        "metadata",
        "prev_hash",
        "row_hash",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request) -> bool:  # pragma: no cover — admin UI hardening
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # pragma: no cover
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # pragma: no cover
        return False
