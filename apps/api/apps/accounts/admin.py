"""Django admin registration for the User model — keeps superuser access intact."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


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
