# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_counter_sellers'),
    ]

    operations = [
        migrations.AddField(
            model_name='refilling',
            name='is_validated',
            field=models.BooleanField(default=False, verbose_name='is validated'),
        ),
        migrations.AddField(
            model_name='selling',
            name='is_validated',
            field=models.BooleanField(default=False, verbose_name='is validated'),
        ),
        migrations.AddField(
            model_name='selling',
            name='label',
            field=models.CharField(max_length=30, default='troll', verbose_name='label'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='selling',
            name='product',
            field=models.ForeignKey(related_name='sellings', to='counter.Product', blank=True),
        ),
    ]
