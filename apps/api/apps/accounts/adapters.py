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
        user.status = "email_unverified"

        if commit:
            user.save()
        return user

    def get_email_confirmation_url(self, request: HttpRequest, emailconfirmation: Any) -> str:
        """Return the Next.js verify-email URL embedded in the outgoing email.

        Frontend route is `/auth/verify-email?key=<token>`. The host comes from
        `NEXT_PUBLIC_SITE_URL` env var; we fail-fast outside `DEBUG` rather than
        silently fall back to localhost (which would ship localhost links to
        production users).
        """
        site_url = os.environ.get("NEXT_PUBLIC_SITE_URL")
        if not site_url:
            if not settings.DEBUG:
                raise ImproperlyConfigured(
                    "NEXT_PUBLIC_SITE_URL must be set in non-DEBUG environments "
                    "to build email-verification links."
                )
            site_url = "http://localhost:3000"
        site_url = site_url.rstrip("/")
        # allauth's HMAC token can contain `=`, `+`, `/`; URL-encode to survive mailer rewrites.
        key = quote(emailconfirmation.key, safe="")
        return f"{site_url}/auth/verify-email?key={key}"
