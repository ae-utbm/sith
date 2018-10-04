# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("accounting", "0004_auto_20161005_1505")]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="remark",
            field=models.CharField(
                null=True, max_length=128, blank=True, verbose_name="comment"
            ),
        )
    ]
