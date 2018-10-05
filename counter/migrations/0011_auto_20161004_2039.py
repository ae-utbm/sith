# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0010_auto_20161003_1900")]

    operations = [
        migrations.AlterField(
            model_name="eticket",
            name="banner",
            field=models.ImageField(
                null=True, verbose_name="banner", blank=True, upload_to="etickets"
            ),
        )
    ]
