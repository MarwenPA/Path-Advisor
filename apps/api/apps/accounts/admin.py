"""Django admin registration for the User model — keeps superuser access intact."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import ParentalConsent, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Slim admin — Story 9.x will add proper back-office filtering."""

    ordering = ("email",)
    list_display = ("email", "role", "status", "is_staff", "created_at")
    list_filter = ("role", "status", "is_staff", "is_superuser")
    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Path-Advisor",
            {
                "fields": (
                    "role",
                    "status",
                    "birth_date",
                    "email_verified_at",
                    "consent_rgpd_at",
                    "consent_cgu_version",
                    "tenant_id",
                )
            },
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")

    def has_add_permission(self, request) -> bool:  # type: ignore[override]
        """Force user creation through the signup flow.

        The admin "Add user" form omits `birth_date` and `consent_rgpd_at`, which would
        let staff create accounts that bypass every guarantee from the serializer
        (CWE-203 enumeration, GDPR consent traceability). The signup endpoint or
        `python manage.py createsuperuser` are the only legitimate paths.
        """
        return False


@admin.register(ParentalConsent)
class ParentalConsentAdmin(admin.ModelAdmin):
    """Read-mostly admin for parental consents (Story 1.4 T1.3).

    Staff can inspect a pending consent but cannot grant/refuse on a parent's behalf —
    that would forge the audit trail. Decisions only flow through `/decide/` with a
    real `content_hash` from the parent's `ConsentDialog` interaction.
    """

    list_display = ("student", "parent_email", "decision", "requested_at", "decided_at")
    list_filter = ("decision",)
    search_fields = ("student__email", "parent_email", "token")
    readonly_fields = (
        "id",
        "student",
        "parent_email",
        "parent_user_id",
        "token",
        "requested_at",
        "expires_at",
        "reminder_sent_at",
        "decision",
        "decided_at",
        "content_hash",
        "decision_ip_truncated",
        "decision_user_agent",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request) -> bool:  # type: ignore[override]
        # Consents are only created by the signup flow — adding from the admin would
        # bypass token generation and email dispatch (and would have no `student` link).
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # type: ignore[override]
        # Deleting a consent would leak the AuditLog row's `subject_id` integrity guarantee.
        return False
