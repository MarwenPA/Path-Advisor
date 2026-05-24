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
            module_name = f"{app_config.name}.exporters"
            try:
                import_module(module_name)
            except ModuleNotFoundError as exc:
                # Only swallow the absence of `<app>.exporters` itself.
                # A transitive `ModuleNotFoundError` raised by code INSIDE an
                # existing `exporters.py` (missing dep, typo in import) must
                # propagate so the app fails loud at startup instead of
                # silently shipping with an incomplete export
                # (post-review patch 2026-05-24).
                if exc.name == module_name:
                    continue
                raise
