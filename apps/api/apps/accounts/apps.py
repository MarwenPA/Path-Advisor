from importlib import import_module

from django.apps import AppConfig, apps


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"

    def ready(self) -> None:
        # Import for side-effects: registers the email_confirmed signal handler.
        # Force-load the bundled exporters (accounts, audit) by importing the
        # package — its __init__.py runs the side-effect imports. Story 1.11.
        from apps.accounts import (
            exporters,  # noqa: F401
            signals,  # noqa: F401
        )

        # Autoload any other app's `exporters` module so future stories
        # (bulletins, recommendations, outreach…) only need to ship a file
        # under `apps/<their_app>/exporters.py` with `@register_exporter(...)`.
        for app_config in apps.get_app_configs():
            if app_config.name == self.name:
                continue
            try:
                import_module(f"{app_config.name}.exporters")
            except ModuleNotFoundError:
                # Apps without an exporters module contribute nothing — skip silently.
                continue
