from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounting", "0003_auto_20160824_2203")]

    operations = [
        migrations.CreateModel(
            name="Label",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="label")),
                (
                    "club_account",
                    models.ForeignKey(
                        related_name="labels",
                        verbose_name="club account",
                        to="accounting.ClubAccount",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="operation",
            name="label",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="operations",
                null=True,
                blank=True,
                verbose_name="label",
                to="accounting.Label",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="label", unique_together={("name", "club_account")}
        ),
    ]
