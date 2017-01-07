# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0003_auto_20170105_2138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shoppinglist',
            name='bought_quantity',
        ),
        migrations.RemoveField(
            model_name='shoppinglist',
            name='tobuy_quantity',
        ),
        migrations.AddField(
            model_name='stockitem',
            name='bought_quantity',
            field=models.IntegerField(help_text='quantity bought during the last shopping session', verbose_name='quantity bought', default=6),
        ),
        migrations.AddField(
            model_name='stockitem',
            name='tobuy_quantity',
            field=models.IntegerField(help_text='quantity to buy during the next shopping session', verbose_name='quantity to buy', default=6),
        ),
    ]
