# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0005_auto_20161105_1035")]

    operations = [
        migrations.AddField(
            model_name="sithfile",
            name="is_moderated",
            field=models.BooleanField(verbose_name="is moderated", default=False),
        )
    ]
