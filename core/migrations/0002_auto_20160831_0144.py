# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="sithfile",
            name="name",
            field=models.CharField(verbose_name="file name", max_length=256),
        )
    ]
