"""Signal handlers — wire allauth lifecycle events into Path-Advisor services."""

from __future__ import annotations

from allauth.account.signals import email_confirmed, user_signed_up
from django.dispatch import receiver

from apps.accounts.services.auth_service import mark_email_verified, record_signup_event


@receiver(user_signed_up)
def _on_user_signed_up(sender, request, user, **kwargs) -> None:
    """Persist the signup event in the audit log + emit operational structlog."""
    record_signup_event(user=user)


@receiver(email_confirmed)
def _on_email_confirmed(sender, request, email_address, **kwargs) -> None:
    """Activate the user when they click the email-confirmation link."""
    mark_email_verified(email_address.user)
