# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_auto_20161113_2325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockitem',
            name='effective_quantity',
            field=models.IntegerField(default=0, verbose_name='effective quantity', help_text='number of box'),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='stock_owner',
            field=models.ForeignKey(related_name='items', to='stock.Stock'),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='type',
            field=models.ForeignKey(related_name='stock_items', verbose_name='type', null=True, to='counter.ProductType', blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='unit_quantity',
            field=models.IntegerField(default=0, verbose_name='unit quantity', help_text='number of element in one box'),
        ),
    ]
