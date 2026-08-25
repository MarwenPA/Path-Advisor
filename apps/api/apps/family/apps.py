from django.apps import AppConfig


class FamilyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.family"
    label = "family"

    def ready(self) -> None:
        # Auto-register the ParentLinkSource AccessListSource adapter (Story 6.1
        # §T5.3) — mirrors `apps.profiles.apps.ProfilesConfig.ready()`. Imported
        # here (not at module top) to avoid AppRegistryNotReady.
        from apps.profiles.access_list import registry

        from .access_list.parent_link import ParentLinkSource

        registry.register(ParentLinkSource())
