"""Ensure a `django.contrib.sites.Site` row exists with id=1.

Allauth raises `Site.DoesNotExist` when its `EmailConfirmation.confirm` path runs without
a Site row matching `SITE_ID`. Django seeds `id=1` automatically only on a *fresh*
`contrib.sites` migration, but never on top of an existing `accounts.0001_initial`
already replayed (Story 1.1 reset path, code review §11).
"""

from __future__ import annotations

from django.db import migrations


def _ensure_default_site(apps, schema_editor) -> None:
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=1,
        defaults={
            "domain": "path-advisor.local",
            "name": "Path-Advisor (local)",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("sites", "0002_alter_domain_unique"),
    ]
    operations = [
        migrations.RunPython(_ensure_default_site, reverse_code=migrations.RunPython.noop),
    ]
