from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trombi", "0003_trombicomment_is_moderated")]

    operations = [
        migrations.CreateModel(
            name="TrombiClubMembership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "club",
                    models.CharField(default="", max_length=32, verbose_name="club"),
                ),
                (
                    "role",
                    models.CharField(default="", max_length=64, verbose_name="role"),
                ),
                (
                    "start",
                    models.CharField(default="", max_length=16, verbose_name="start"),
                ),
                (
                    "end",
                    models.CharField(default="", max_length=16, verbose_name="end"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="user",
                        related_name="memberships",
                        to="trombi.TrombiUser",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        )
    ]
