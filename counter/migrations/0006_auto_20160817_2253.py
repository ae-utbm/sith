# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0005_auto_20160817_2251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(blank=True, max_length=16, verbose_name='code'),
        ),
    ]
