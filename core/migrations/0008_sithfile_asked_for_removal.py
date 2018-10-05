# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0006_auto_20161108_1703")]

    operations = [
        migrations.AddField(
            model_name="sithfile",
            name="asked_for_removal",
            field=models.BooleanField(default=False, verbose_name="asked for removal"),
        )
    ]
