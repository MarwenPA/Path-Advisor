"""Django admin registration for early-outreach requests — Story 5.5.

This is the interim moderation tool: a `path_admin` staff account reviews
`pending_moderation` requests here and either approves them (bulk action,
no extra input needed) or rejects them (a reason is mandatory, so it goes
through an intermediate confirmation page — mirrors
`apps.accounts.admin.AccountDeletionRequestAdmin._dpo_cancel_view`). A
dedicated moderation-queue UI is Story 9.4's job; this keeps 5.5 unblocked
without building throwaway API+frontend for something the back-office epic
will eventually own.
"""

from __future__ import annotations

from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from apps.outreach.exceptions import OutreachModerationStateError
from apps.outreach.models import EarlyOutreachRequest, EarlyOutreachResponse
from apps.outreach.services.early_outreach import (
    approve_early_outreach_motivation,
    reject_early_outreach_motivation,
)


@admin.register(EarlyOutreachRequest)
class EarlyOutreachRequestAdmin(admin.ModelAdmin):
    """Read-mostly — the only mutations are the moderation actions below.
    Manually creating/editing/deleting a request here would bypass the
    quota check and the audit trail the service layer writes."""

    list_display = (
        "id",
        "student",
        "school",
        "profession",
        "status",
        "created_at",
        "_reject_action_link",
    )
    list_filter = ("status",)
    search_fields = ("id", "student__email", "school__name")
    readonly_fields = (
        "id",
        "student",
        "school",
        "profession",
        "parcours",
        "motivation_text",
        "status",
        "rejection_reason",
        "created_at",
        "updated_at",
    )
    actions = ["approve_motivation"]

    def has_add_permission(self, request: HttpRequest) -> bool:  # type: ignore[override]
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:  # type: ignore[override]
        return False

    @admin.display(description="Rejeter")
    def _reject_action_link(self, obj: EarlyOutreachRequest):
        if obj.status != "pending_moderation":
            return "—"
        url = reverse("admin:outreach_earlyoutreachrequest_reject_motivation", args=[obj.pk])
        return format_html('<a href="{}">Rejeter (raison)</a>', url)

    @admin.action(description="Approuver la motivation (débloque l'envoi vers l'école)")
    def approve_motivation(self, request: HttpRequest, queryset) -> None:
        approved, skipped = 0, 0
        for outreach in queryset:
            try:
                approve_early_outreach_motivation(outreach=outreach)
                approved += 1
            except OutreachModerationStateError:
                skipped += 1
        if approved:
            self.message_user(
                request, f"{approved} motivation(s) approuvée(s).", level=messages.SUCCESS
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} demande(s) ignorée(s) (pas en attente de modération).",
                level=messages.WARNING,
            )

    # --- Custom URL: reject with a mandatory reason -----------------------

    def get_urls(self):  # type: ignore[override]
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/reject-motivation/",
                self.admin_site.admin_view(self._reject_motivation_view),
                name="outreach_earlyoutreachrequest_reject_motivation",
            ),
        ]
        return custom + urls

    def _reject_motivation_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        outreach = EarlyOutreachRequest.objects.filter(pk=object_id).first()
        if outreach is None:
            self.message_user(request, "Demande introuvable.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:outreach_earlyoutreachrequest_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Rejeter la motivation",
            "outreach": outreach,
            "opts": self.model._meta,
            "errors": [],
        }

        if request.method == "POST":
            reason = (request.POST.get("reason") or "").strip()
            if not reason:
                context["errors"] = ["Une raison non vide est obligatoire."]
                return TemplateResponse(
                    request, "admin/outreach/reject_motivation_confirm.html", context
                )
            try:
                reject_early_outreach_motivation(outreach=outreach, reason=reason)
            except OutreachModerationStateError:
                self.message_user(
                    request,
                    "Cette demande n'est plus en attente de modération.",
                    level=messages.WARNING,
                )
            else:
                self.message_user(request, "Motivation rejetée.", level=messages.SUCCESS)
            return HttpResponseRedirect(reverse("admin:outreach_earlyoutreachrequest_changelist"))

        return TemplateResponse(request, "admin/outreach/reject_motivation_confirm.html", context)


@admin.register(EarlyOutreachResponse)
class EarlyOutreachResponseAdmin(admin.ModelAdmin):
    """Story 5.7 — read-only. `comment` isn't gated by an a-priori
    moderation queue (see the model's docstring for why); this admin is
    the reactive-moderation surface a path_admin can use if a comment is
    ever reported as inappropriate — no bulk action needed for that, just
    visibility."""

    list_display = ("id", "request", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("id", "request__id", "request__student__email")
    readonly_fields = (
        "id",
        "request",
        "action",
        "comment",
        "proposed_slots",
        "accepted_slot",
        "alternative_note",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:  # type: ignore[override]
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:  # type: ignore[override]
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:  # type: ignore[override]
        return False
