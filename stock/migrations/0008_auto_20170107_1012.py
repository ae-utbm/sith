# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0007_shoppinglistitem_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppinglistitem',
            name='stockitem_owner',
            field=models.ForeignKey(related_name='shopping_item', to='stock.StockItem', null=True),
        ),
    ]
