# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("club", "0002_auto_20160824_2152")]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="start_date",
            field=models.DateField(verbose_name="start date"),
        )
    ]
