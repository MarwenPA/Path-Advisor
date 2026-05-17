from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"

    def ready(self) -> None:
        # Import for side-effects: registers the email_confirmed signal handler.
        from apps.accounts import signals  # noqa: F401
