# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_auto_20161004_2039'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingList',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(verbose_name='date')),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('todo', models.BooleanField(verbose_name='todo')),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('counter', models.OneToOneField(to='counter.Counter', verbose_name='counter', related_name='stock')),
            ],
        ),
        migrations.CreateModel(
            name='StockItem',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('unit_quantity', models.IntegerField(default=0, help_text='number of element in one box', verbose_name='unit quantity')),
                ('effective_quantity', models.IntegerField(default=0, help_text='number of box', verbose_name='effective quantity')),
                ('stock_owner', models.ForeignKey(to='stock.Stock', related_name='items')),
                ('type', models.ForeignKey(to='counter.ProductType', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='type', blank=True, related_name='stock_items')),
            ],
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='items_to_buy',
            field=models.ManyToManyField(to='stock.StockItem', related_name='shopping_lists', verbose_name='items to buy'),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='stock_owner',
            field=models.ForeignKey(to='stock.Stock', null=True, related_name='shopping_lists'),
        ),
    ]
