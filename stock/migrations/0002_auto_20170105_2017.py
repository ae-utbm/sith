# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='bought_quantity',
            field=models.IntegerField(help_text='quantity bought during the last shopping session', default=6, verbose_name='quantity bought'),
        ),
        migrations.AddField(
            model_name='stockitem',
            name='minimal_quantity',
            field=models.IntegerField(help_text='if the effective quantity is less than the minimal, item is added to the shopping list', default=1, verbose_name='minimal quantity'),
        ),
        migrations.AddField(
            model_name='stockitem',
            name='tobuy_quantity',
            field=models.IntegerField(help_text='quantity to buy during the next shopping session', default=6, verbose_name='quantity to buy'),
        ),
    ]
