# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, serialize=False, primary_key=True)),
                ('account_id', models.CharField(max_length=10, verbose_name='account id', unique=True)),
            ],
            options={
                'verbose_name': 'customer',
                'verbose_name_plural': 'customers',
            },
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(default=None, blank=True, null=True, verbose_name='end date')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('closed', models.BooleanField(default=False, verbose_name='is closed')),
            ],
        ),
        migrations.CreateModel(
            name='GenericInvoice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('journal', models.ForeignKey(to='accounting.GeneralJournal', related_name='invoices')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('code', models.CharField(max_length=10, verbose_name='code')),
                ('purchase_price', accounting.models.CurrencyField(max_digits=12, verbose_name='purchase price', decimal_places=2)),
                ('selling_price', accounting.models.CurrencyField(max_digits=12, verbose_name='selling price', decimal_places=2)),
                ('special_selling_price', accounting.models.CurrencyField(max_digits=12, verbose_name='special selling price', decimal_places=2)),
                ('icon', models.ImageField(upload_to='products', blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('icon', models.ImageField(upload_to='products', blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(blank=True, related_name='products', to='accounting.ProductType', null=True),
        ),
    ]
