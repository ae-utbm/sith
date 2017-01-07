# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0004_auto_20170105_2145'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingListItems',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('tobuy_quantity', models.IntegerField(verbose_name='quantity to buy', default=6, help_text='quantity to buy during the next shopping session')),
                ('bought_quantity', models.IntegerField(verbose_name='quantity bought', default=6, help_text='quantity bought during the last shopping session')),
            ],
        ),
        migrations.RemoveField(
            model_name='stockitem',
            name='bought_quantity',
        ),
        migrations.RemoveField(
            model_name='stockitem',
            name='tobuy_quantity',
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='comment',
            field=models.TextField(null=True, verbose_name='comment', blank=True),
        ),
        migrations.AddField(
            model_name='shoppinglistitems',
            name='shoppinglist_owner',
            field=models.ForeignKey(related_name='item_quantity', to='stock.ShoppingList'),
        ),
        migrations.AddField(
            model_name='shoppinglistitems',
            name='stockitem_owner',
            field=models.ForeignKey(related_name='item', null=True, to='stock.StockItem'),
        ),
    ]
