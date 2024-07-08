# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0026_auto_20170926_1512")]

    operations = [
        migrations.CreateModel(
            name="Gift",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                    ),
                ),
                ("label", models.CharField(max_length=255, verbose_name="label")),
                (
                    "date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gifts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        )
    ]
