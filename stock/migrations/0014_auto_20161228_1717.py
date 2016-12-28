# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0013_auto_20161228_1006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppinglist',
            name='stock_owner',
            field=models.ForeignKey(related_name='shopping_lists', null=True, to='stock.Stock'),
        ),
    ]
