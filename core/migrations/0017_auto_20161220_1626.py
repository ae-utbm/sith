# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0016_auto_20161212_1922")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="last_update",
            field=models.DateTimeField(verbose_name="last update", auto_now=True),
        )
    ]
