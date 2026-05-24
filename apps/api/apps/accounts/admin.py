"""Django admin registration for the User model — keeps superuser access intact."""

from __future__ import annotations

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from apps.accounts.gdpr_exceptions import (
    AccountDeletionAlreadyResolved,
    AccountDeletionExpired,
)
from apps.accounts.models import AccountDeletionRequest, ParentalConsent, User


def _has_explicit_dpo_perm(user) -> bool:
    """Strict permission check that bypasses `is_superuser` shortcut (Story 1.12 §D1).

    Django's default `has_perm()` returns True unconditionally for `is_superuser=True`,
    which the spec AC9 explicitly rejects: "the DPO must have the explicit
    `cancel_deletion_request` perm; `is_superuser=True` alone is NOT sufficient".

    We query `auth_permission` directly via the user's groups + direct grants
    so the superuser short-circuit doesn't apply. The active-and-authenticated
    guards mirror Django's own `has_perm` so a deactivated DPO doesn't slip
    through.
    """
    from django.contrib.auth.models import Permission
    from django.db.models import Q

    if not user.is_active or not user.is_authenticated:
        return False
    return (
        Permission.objects.filter(
            codename="cancel_deletion_request",
            content_type__app_label="accounts",
        )
        .filter(Q(user=user) | Q(group__user=user))
        .exists()
    )


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


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    """DPO admin for in-flight + historical account-deletion requests (Story 1.12 §AC9).

    Read-only by default. The single mutation surface is the `cancel_deletion_dpo`
    custom action: it walks the operator through a confirmation page collecting a
    free-form `cancel_reason`, then delegates to `account_deletion_service.cancel_deletion`
    with `password=None` (the privileged path) and `actor=request.user`. The audit
    log row is written by the service decorator with `actor_id=<dpo_id>` so the
    DPO action is unambiguously attributable.

    Permission: `accounts.cancel_deletion_request` (declared on the model Meta).
    Granting it requires an explicit superuser-level action — `is_superuser=True`
    alone is NOT sufficient to perform the cancellation.
    """

    list_display = (
        "id",
        "user_id_snapshot",
        "_state_label",
        "requested_at",
        "hard_delete_after",
        "hard_delete_attempt_count",
        "_dpo_action_link",
    )
    list_filter = ("hard_deleted_at", "cancelled_at")
    search_fields = ("id", "user_id_snapshot", "cancel_token")
    readonly_fields = (
        "id",
        "user",
        "user_id_snapshot",
        "cancel_token",
        "requested_at",
        "hard_delete_after",
        "cancelled_at",
        "cancel_reason",
        "hard_deleted_at",
        "hard_delete_attempt_count",
        "last_failure_code",
        "requested_ip_truncated",
        "requested_user_agent",
        # Note: `password_hash_at_request` is intentionally NOT in readonly_fields —
        # the field is omitted from `fieldsets` below so it's never rendered.
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "user", "user_id_snapshot", "cancel_token")}),
        (
            "Lifecycle",
            {
                "fields": (
                    "requested_at",
                    "hard_delete_after",
                    "cancelled_at",
                    "cancel_reason",
                    "hard_deleted_at",
                    "hard_delete_attempt_count",
                    "last_failure_code",
                )
            },
        ),
        (
            "Forensics",
            {"fields": ("requested_ip_truncated", "requested_user_agent")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="State")
    def _state_label(self, obj: AccountDeletionRequest) -> str:
        if obj.hard_deleted_at:
            return "hard_deleted"
        if obj.cancelled_at:
            return "cancelled"
        if obj.is_past_grace_window:
            return "expired"
        return "pending"

    @admin.display(description="DPO action")
    def _dpo_action_link(self, obj: AccountDeletionRequest) -> str:
        # Only surface the override link for rows that can still be cancelled.
        if obj.cancelled_at or obj.hard_deleted_at or obj.is_past_grace_window:
            return "—"
        # Story 1.12 code review §P23: only `NoReverseMatch` is an expected
        # failure mode here (URL renamed); other exceptions deserve to bubble
        # so the operator sees the real bug rather than a silent `—`.
        from django.urls.exceptions import NoReverseMatch

        try:
            url = reverse(
                "admin:accounts_accountdeletionrequest_dpo_cancel",
                args=(obj.pk,),
            )
        except NoReverseMatch:
            log = __import__("structlog").get_logger(__name__)
            log.warning(
                "accounts.admin.dpo_action_link_unreachable",
                deletion_request_id=obj.pk,
            )
            return "—"
        return format_html(
            '<a class="button" href="{}">Cancel (DPO)</a>',
            url,
        )

    def has_add_permission(self, request: HttpRequest) -> bool:  # type: ignore[override]
        # Requests only originate from the user's own POST — admin add would
        # bypass the password re-auth + the audit decorator.
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:  # type: ignore[override]
        # Read-only: the only legitimate mutation is via the `cancel_deletion_dpo`
        # action below, which has its own permission check.
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:  # type: ignore[override]
        # Deleting the row would erase the audit artifact (3-year retention obligation).
        return False

    # --- Custom URL: DPO override cancel ---------------------------------------

    def get_urls(self):  # type: ignore[override]
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/dpo-cancel/",
                self.admin_site.admin_view(self._dpo_cancel_view),
                name="accounts_accountdeletionrequest_dpo_cancel",
            ),
        ]
        return custom + urls

    def _dpo_cancel_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        """Intermediate confirmation page collecting `cancel_reason`, then dispatching."""
        # Lazy imports — keep the admin module light at startup.
        from apps.accounts.services import account_deletion as deletion_service

        # Story 1.12 code review §D1: enforce strict permission check that
        # bypasses Django's `is_superuser=True` shortcut. The spec AC9 is
        # explicit: granting `cancel_deletion_request` is the DPO grant; a
        # bare superuser must NOT pick up the perm automatically. Direct
        # query against `auth_permission` skips `has_perm()`'s superuser
        # short-circuit.
        if not _has_explicit_dpo_perm(request.user):
            self.message_user(
                request,
                "Permission refusée: il faut le droit explicite `accounts.cancel_deletion_request` "
                "(le statut superuser seul ne suffit pas).",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(reverse("admin:accounts_accountdeletionrequest_changelist"))

        deletion = AccountDeletionRequest.objects.filter(pk=object_id).first()
        if deletion is None:
            self.message_user(request, "Demande introuvable.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:accounts_accountdeletionrequest_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Annuler la demande de suppression (DPO)",
            "deletion": deletion,
            "opts": self.model._meta,
            "user_id_snapshot": deletion.user_id_snapshot,
            "errors": [],
        }

        if request.method == "POST":
            # Story 1.12 code review §P10: re-check the permission inside the
            # POST branch — guards against the rare case where the DPO loses
            # the perm between page render (GET) and form submit (POST).
            if not _has_explicit_dpo_perm(request.user):
                self.message_user(
                    request,
                    "Permission révoquée entre l'ouverture du formulaire et la soumission.",
                    level=messages.ERROR,
                )
                return HttpResponseRedirect(
                    reverse("admin:accounts_accountdeletionrequest_changelist")
                )

            cancel_reason = (request.POST.get("cancel_reason") or "").strip()
            if not cancel_reason:
                context["errors"] = ["Une raison non vide est obligatoire."]
                return TemplateResponse(
                    request,
                    "admin/accounts/cancel_deletion_confirm.html",
                    context,
                )
            try:
                deletion_service.cancel_deletion(
                    request=deletion,
                    password=None,
                    actor=request.user,
                    cancel_reason=f"dpo_override:{request.user.id}:{cancel_reason}",
                )
            except AccountDeletionAlreadyResolved:
                self.message_user(
                    request,
                    "Cette demande est déjà annulée ou exécutée.",
                    level=messages.WARNING,
                )
            except AccountDeletionExpired:
                self.message_user(
                    request,
                    "La fenêtre d'annulation est dépassée — la suppression a déjà eu lieu ou va survenir.",
                    level=messages.WARNING,
                )
            else:
                self.message_user(
                    request,
                    f"Compte restauré (raison enregistrée: {cancel_reason}).",
                    level=messages.SUCCESS,
                )
            return HttpResponseRedirect(reverse("admin:accounts_accountdeletionrequest_changelist"))

        return TemplateResponse(
            request,
            "admin/accounts/cancel_deletion_confirm.html",
            context,
        )
