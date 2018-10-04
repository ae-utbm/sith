# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Sith",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "alert_msg",
                    models.TextField(
                        default="", verbose_name="alert message", blank=True
                    ),
                ),
                (
                    "info_msg",
                    models.TextField(
                        default="", verbose_name="info message", blank=True
                    ),
                ),
                (
                    "index_page",
                    models.TextField(default="", verbose_name="index page", blank=True),
                ),
            ],
        )
    ]
