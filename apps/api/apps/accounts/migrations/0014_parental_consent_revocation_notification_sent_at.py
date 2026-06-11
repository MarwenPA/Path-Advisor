"""Story 1.10 review D5 — add ``parental_consents.revocation_notification_sent_at``.

The Story 1.10 ``notify_parental_consent_revoked`` Celery task uses this
column to gate idempotent re-sends (Story 1.4 pattern from
``notify_unconfirmed_granted_consents``). Without it, a Celery retry after a
transient SMTP failure can re-deliver the same email.

Distinct from ``notification_sent_at`` (Story 1.4) which tracks the *granted*
email — using one column for both would conflict on a consent that was
granted, then later revoked.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_parental_consent_revoked_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="parentalconsent",
            name="revocation_notification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
