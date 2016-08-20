# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0016_auto_20160820_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='parent_product',
            field=models.ForeignKey(to='counter.Product', null=True, related_name='children_products', on_delete=django.db.models.deletion.SET_NULL, verbose_name='parent product', blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(to='counter.ProductType', null=True, related_name='products', on_delete=django.db.models.deletion.SET_NULL, verbose_name='product type', blank=True),
        ),
    ]
