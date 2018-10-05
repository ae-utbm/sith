# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0008_counter_token")]

    operations = [
        migrations.CreateModel(
            name="Eticket",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "banner",
                    models.ImageField(null=True, upload_to="etickets", blank=True),
                ),
                (
                    "secret",
                    models.CharField(unique=True, verbose_name="secret", max_length=64),
                ),
                (
                    "product",
                    models.OneToOneField(
                        verbose_name="product",
                        related_name="eticket",
                        to="counter.Product",
                    ),
                ),
            ],
        )
    ]
