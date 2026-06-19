from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("bulletins", "0001_initial"),
        ("students", "0004_bulletins_postponed_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="BulletinManual",
            fields=[
                ("id", models.CharField(default=None, editable=False, max_length=32, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("trimestre_label", models.CharField(max_length=20)),
                ("year", models.CharField(max_length=10)),
                ("level_at_save", models.CharField(blank=True, max_length=30)),
                ("subjects_ref_version", models.CharField(blank=True, max_length=20)),
                ("matieres", models.JSONField(default=list)),
                ("source", models.CharField(default="manual", editable=False, max_length=10)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manual_bulletins",
                        to="students.studentprofile",
                    ),
                ),
            ],
            options={"db_table": "bulletin_manuals"},
        ),
    ]
