# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_auto_20161004_2039'),
        ('stock', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='type',
            field=models.ForeignKey(to='counter.ProductType', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='type', related_name='stockItem_type'),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='effective_quantity',
            field=models.IntegerField(help_text='total number of bottle/barrel', verbose_name='effective quantity', default=0),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='unit_quantity',
            field=models.IntegerField(help_text='number of beer in one crate (equal one for barrels)', verbose_name='unit quantity', default=0),
        ),
    ]
