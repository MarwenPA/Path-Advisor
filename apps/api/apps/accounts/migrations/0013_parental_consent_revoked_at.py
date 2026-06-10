"""Story 1.9 §AC1 / §4.6 — add ``parental_consents.revoked_at``.

The column is nullable (default NULL = active grant). Story 1.9 only READS
this column ; Story 1.10 will write to it on user-initiated revocation.

A composite index ``(student_id, revoked_at)`` keeps the access-list query
``WHERE student_id = :u AND revoked_at IS NULL`` fast even on the (unlikely)
worst-case of a student with many parental consents over time.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_user_role_support"),
    ]

    operations = [
        migrations.AddField(
            model_name="parentalconsent",
            name="revoked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="parentalconsent",
            index=models.Index(
                fields=["student", "revoked_at"],
                name="parental_co_student_revoke_idx",
            ),
        ),
    ]
