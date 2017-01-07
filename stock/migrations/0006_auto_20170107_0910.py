# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0005_auto_20170107_0857'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingListItem',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('tobuy_quantity', models.IntegerField(default=6, help_text='quantity to buy during the next shopping session', verbose_name='quantity to buy')),
                ('bought_quantity', models.IntegerField(default=0, help_text='quantity bought during the last shopping session', verbose_name='quantity bought')),
            ],
        ),
        migrations.RemoveField(
            model_name='shoppinglistitems',
            name='shoppinglist_owner',
        ),
        migrations.RemoveField(
            model_name='shoppinglistitems',
            name='stockitem_owner',
        ),
        migrations.RemoveField(
            model_name='shoppinglist',
            name='items_to_buy',
        ),
        migrations.DeleteModel(
            name='ShoppingListItems',
        ),
        migrations.AddField(
            model_name='shoppinglistitem',
            name='shopping_lists',
            field=models.ManyToManyField(related_name='shopping_items_to_buy', to='stock.ShoppingList', verbose_name='shopping lists'),
        ),
        migrations.AddField(
            model_name='shoppinglistitem',
            name='stockitem_owner',
            field=models.ForeignKey(related_name='item', null=True, to='stock.StockItem'),
        ),
    ]
