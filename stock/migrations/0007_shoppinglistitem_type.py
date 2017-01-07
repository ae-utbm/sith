# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_auto_20161004_2039'),
        ('stock', '0006_auto_20170107_0910'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppinglistitem',
            name='type',
            field=models.ForeignKey(null=True, verbose_name='type', on_delete=django.db.models.deletion.SET_NULL, to='counter.ProductType', blank=True, related_name='shoppinglist_items'),
        ),
    ]
