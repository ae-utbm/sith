# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0004_auto_20160817_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(verbose_name='code', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
    ]
