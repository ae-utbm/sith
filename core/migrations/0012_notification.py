# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("core", "0011_auto_20161124_0848")]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("url", models.CharField(max_length=255, verbose_name="url")),
                ("text", models.CharField(max_length=512, verbose_name="text")),
                (
                    "type",
                    models.CharField(
                        max_length=16,
                        choices=[
                            ("FILE_MODERATION", "File moderation"),
                            ("SAS_MODERATION", "SAS moderation"),
                            ("NEW_PICTURES", "New pictures"),
                        ],
                        verbose_name="text",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "date",
                    models.DateTimeField(
                        verbose_name="date", default=django.utils.timezone.now
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="notifications", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        )
    ]
