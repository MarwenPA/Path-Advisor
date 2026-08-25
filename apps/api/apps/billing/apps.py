from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Billing & Subscriptions"

    def ready(self) -> None:
        # Register the pre_delete Stripe-cancellation signal (Story 5.2).
        from apps.billing import signals  # noqa: F401
