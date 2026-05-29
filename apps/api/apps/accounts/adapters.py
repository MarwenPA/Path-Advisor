"""allauth adapter — bridges allauth's signup flow to our custom User model.

Two responsibilities:
- Apply the Path-Advisor fields (`role`, `birth_date`, `consent_rgpd_at`, etc.)
  that allauth's default `save_user` does not know about.
- Build the email-confirmation URL pointing at the Next.js front (the user
  experience is a SPA redirect, not the django-served allauth template).
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils import timezone


class PathAdvisorAccountAdapter(DefaultAccountAdapter):
    """Override allauth defaults so signup writes our custom User columns."""

    def save_user(self, request: HttpRequest, user: Any, form: Any, commit: bool = True) -> Any:
        # `form` may be a dj-rest-auth serializer or a Django form depending on the entry point.
        cleaned = (
            form.cleaned_data if hasattr(form, "cleaned_data") else form.validated_data  # type: ignore[union-attr]
        )

        user = super().save_user(request, user, form, commit=False)
        user.role = "student"
        user.birth_date = cleaned.get("birth_date")
        # Strict `is True` comparison: truthy non-bool values (1, "true", non-empty strings)
        # must not be treated as a valid GDPR consent — silent data-quality issue otherwise.
        user.consent_rgpd_at = (
            timezone.now() if cleaned.get("consent_rgpd_accepted") is True else None
        )
        user.consent_cgu_version = cleaned.get("consent_cgu_version")

        # Story 1.4 branching: presence of a `parent_email` flags the minor flow. The
        # `email_verified_at` field stays NULL either way — the child must independently
        # verify their email (cf. AC3 state machine), parental consent is orthogonal.
        parent_email = cleaned.get("parent_email")
        if parent_email:
            user.status = "pending_parental_consent"
        else:
            user.status = "email_unverified"

        if commit:
            user.save()
        # Pass the parent_email through to the `user_signed_up` signal via a transient
        # attribute — allauth fires the signal with a plain WSGIRequest (not a DRF
        # Request), so `request.data` is unavailable in the handler. Re-reading the
        # body there would force a second JSON parse and tie us to a Content-Type.
        user._parent_email_pending = parent_email  # type: ignore[attr-defined]
        return user

    def get_email_confirmation_url(self, request: HttpRequest, emailconfirmation: Any) -> str:
        """Return the Next.js verify-email URL embedded in the outgoing email.

        Frontend route is `/auth/verify-email?key=<token>`. Host resolution
        via `_resolve_site_url`.
        """
        site_url = self._resolve_site_url()
        # allauth's HMAC token can contain `=`, `+`, `/`; URL-encode to survive mailer rewrites.
        key = quote(emailconfirmation.key, safe="")
        return f"{site_url}/auth/verify-email?key={key}"

    def get_password_reset_url(self, request: HttpRequest, uid: str, token: str) -> str:
        """Return the Next.js password-reset URL — Story 1.5 §AC5.

        Front-end route: `/auth/reset-password/<uid>/<token>`. Same host-
        resolution policy as `get_email_confirmation_url` — fail-fast in
        non-DEBUG when `NEXT_PUBLIC_SITE_URL` is unset.
        """
        site_url = self._resolve_site_url()
        safe_uid = quote(uid, safe="")
        safe_token = quote(token, safe="")
        return f"{site_url}/auth/reset-password/{safe_uid}/{safe_token}"

    def _resolve_site_url(self) -> str:
        """Shared host-resolution for auth-flow emails.

        Fail-fast in non-DEBUG keeps a missing `NEXT_PUBLIC_SITE_URL` from
        shipping localhost links to real users.
        """
        site_url = os.environ.get("NEXT_PUBLIC_SITE_URL")
        if not site_url:
            if not settings.DEBUG:
                raise ImproperlyConfigured(
                    "NEXT_PUBLIC_SITE_URL must be set in non-DEBUG environments "
                    "to build auth-flow links."
                )
            site_url = "http://localhost:3000"
        return site_url.rstrip("/")

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        """Render + dispatch transactional emails under the `fr-FR` locale.

        Story 1.5 §AC11 carries the locale-override fix from Story 1.12 §P21
        forward: Celery workers (or sync callers with a system locale of
        en-US) would otherwise render `{{ ...|date }}` filters in English.
        Wrapping the render in `translation.override("fr-FR")` guarantees
        FR month names regardless of worker locale.
        """
        from django.utils import translation

        with translation.override("fr-FR"):
            return super().send_mail(template_prefix, email, context)
