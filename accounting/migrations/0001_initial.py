# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20160128_0842'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, primary_key=True, serialize=False)),
                ('account_id', models.CharField(unique=True, verbose_name='account id', max_length=10)),
            ],
            options={
                'verbose_name': 'customer',
                'verbose_name_plural': 'customers',
            },
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(null=True, verbose_name='end date', blank=True, default=None)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('closed', models.BooleanField(default=False, verbose_name='is closed')),
            ],
        ),
        migrations.CreateModel(
            name='GenericInvoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=100)),
                ('journal', models.ForeignKey(to='accounting.GeneralJournal', related_name='invoices')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('description', models.TextField(verbose_name='description')),
                ('code', models.CharField(verbose_name='code', max_length=10)),
                ('purchase_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='purchase price')),
                ('selling_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='selling price')),
                ('special_selling_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='special selling price')),
                ('icon', models.ImageField(null=True, upload_to='products')),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('description', models.TextField(verbose_name='description')),
                ('icon', models.ImageField(null=True, upload_to='products')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(null=True, to='accounting.ProductType', related_name='products'),
        ),
    ]
