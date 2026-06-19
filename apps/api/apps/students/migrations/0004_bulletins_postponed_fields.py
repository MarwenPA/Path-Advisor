from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0003_maturity_celebration_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="bulletins_postponed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="bulletins_postponed_banner_dismissed_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
