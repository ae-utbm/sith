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
                ('user', models.OneToOneField(primary_key=True, to=settings.AUTH_USER_MODEL, serialize=False)),
                ('account_id', models.CharField(max_length=10, unique=True, verbose_name='account id')),
            ],
            options={
                'verbose_name_plural': 'customers',
                'verbose_name': 'customer',
            },
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(blank=True, default=None, null=True, verbose_name='end date')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('closed', models.BooleanField(default=False, verbose_name='is closed')),
            ],
        ),
        migrations.CreateModel(
            name='GenericInvoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('journal', models.ForeignKey(related_name='invoices', to='accounting.GeneralJournal')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('code', models.CharField(max_length=10, verbose_name='code')),
                ('purchase_price', accounting.models.CurrencyField(decimal_places=2, max_digits=12, verbose_name='purchase price')),
                ('selling_price', accounting.models.CurrencyField(decimal_places=2, max_digits=12, verbose_name='selling price')),
                ('special_selling_price', accounting.models.CurrencyField(decimal_places=2, max_digits=12, verbose_name='special selling price')),
                ('icon', models.ImageField(blank=True, upload_to='products', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('icon', models.ImageField(blank=True, upload_to='products', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(related_name='products', blank=True, to='accounting.ProductType', null=True),
        ),
    ]
