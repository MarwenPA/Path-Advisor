# Generated for Story 1.11 — post-review patch (decision D4, 2026-05-24).
#
# Adds a PostgreSQL partial unique index so two simultaneous POSTs cannot
# both pass the application-level `_has_active_export` guard and create two
# pending/in_progress rows for the same user (race surfaced by Edge Case
# Hunter). The 2nd concurrent INSERT now raises IntegrityError, which the
# service translates back into `GdprExportInProgress` (409).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_gdpr_export_request"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="gdprexportrequest",
            constraint=models.UniqueConstraint(
                fields=["user_id"],
                condition=models.Q(status__in=("pending", "in_progress")),
                name="uniq_gdpr_active_per_user",
            ),
        ),
    ]
