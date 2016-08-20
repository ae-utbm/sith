# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0014_auto_20160819_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='limit_age',
            field=models.IntegerField(default=0, verbose_name='limit age'),
        ),
        migrations.AddField(
            model_name='product',
            name='tray',
            field=models.BooleanField(default=False, verbose_name='tray price'),
        ),
    ]
