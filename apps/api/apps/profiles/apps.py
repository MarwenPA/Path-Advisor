from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    label = "profiles"

    def ready(self) -> None:
        # Auto-register every AccessListSource adapter on app startup.
        # Imported here (not at module top) to avoid AppRegistryNotReady — the
        # adapters reference `apps.accounts.models` which needs the app registry.
        from .access_list import registry
        from .access_list.sources.parental_consent import ParentalConsentSource

        registry.register(ParentalConsentSource())
