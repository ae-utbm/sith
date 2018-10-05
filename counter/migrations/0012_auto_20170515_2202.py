# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0011_auto_20161004_2039")]

    operations = [
        migrations.AlterField(
            model_name="permanency",
            name="end",
            field=models.DateTimeField(
                db_index=True, verbose_name="end date", null=True
            ),
        )
    ]
