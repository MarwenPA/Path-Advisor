"""Migration for Story 4.7 — adapt Parcours model for niveau scolaire filtering.

Changes from Story 4.3 baseline (0002_parcours):
- Add `label` CharField(max_length=200, blank=True)
- Add `updated_at` DateTimeField(auto_now=True)
- Make `target_school` nullable (SET_NULL) to support parcours without a target school
- Remove unique_together constraint (profession, target_school, niveau_scolaire)
- Add partial UniqueConstraint: at most one is_default=True per (profession, niveau_scolaire)
- Add composite index on (profession, niveau_scolaire)
"""

from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0002_parcours"),
    ]

    operations = [
        # 1. Add label field
        migrations.AddField(
            model_name="parcours",
            name="label",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Short descriptive label for this parcours alternative.",
                max_length=200,
            ),
            preserve_default=False,
        ),
        # 2. Add updated_at field
        migrations.AddField(
            model_name="parcours",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        # 3. Make target_school nullable (SET_NULL instead of CASCADE)
        migrations.AlterField(
            model_name="parcours",
            name="target_school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="parcours",
                to="schools.school",
            ),
        ),
        # 4. Remove old unique_together constraint
        migrations.AlterUniqueTogether(
            name="parcours",
            unique_together=set(),
        ),
        # 5. Add composite index on (profession, niveau_scolaire)
        migrations.AddIndex(
            model_name="parcours",
            index=models.Index(
                fields=["profession", "niveau_scolaire"],
                name="schools_par_profess_47_idx",
            ),
        ),
        # 6. Add partial unique constraint: at most one is_default per (profession, niveau_scolaire)
        migrations.AddConstraint(
            model_name="parcours",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=("profession", "niveau_scolaire"),
                name="parcours_unique_default_per_profession_niveau",
            ),
        ),
    ]
