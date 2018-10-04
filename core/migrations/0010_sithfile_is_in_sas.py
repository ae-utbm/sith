# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0009_auto_20161120_1155")]

    operations = [
        migrations.AddField(
            model_name="sithfile",
            name="is_in_sas",
            field=models.BooleanField(verbose_name="is in the SAS", default=False),
        )
    ]
