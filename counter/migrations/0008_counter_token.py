# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0007_product_archived")]

    operations = [
        migrations.AddField(
            model_name="counter",
            name="token",
            field=models.CharField(
                blank=True, max_length=30, verbose_name="token", null=True
            ),
        )
    ]
