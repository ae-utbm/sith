# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("club", "0005_auto_20161120_1149")]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="start_date",
            field=models.DateField(
                verbose_name="start date", default=django.utils.timezone.now
            ),
        )
    ]
