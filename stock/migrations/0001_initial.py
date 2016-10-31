# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_auto_20161004_2039'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('counter', models.OneToOneField(to='counter.Counter', related_name='stock', verbose_name='counter')),
            ],
        ),
        migrations.CreateModel(
            name='StockItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('unit_quantity', models.IntegerField(default=0, verbose_name='unit quantity')),
                ('effective_quantity', models.IntegerField(default=0, verbose_name='effective quantity')),
                ('stock_owner', models.ForeignKey(related_name='stock_owner', to='stock.Stock')),
            ],
        ),
    ]
