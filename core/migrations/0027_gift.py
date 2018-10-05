# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone


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
                        related_name="gifts", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        )
    ]
