# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('club', '__first__'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('rib', models.CharField(verbose_name='rib', max_length=255)),
                ('number', models.CharField(verbose_name='account number', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ClubAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('bank_account', models.ForeignKey(related_name='club_accounts', to='accounting.BankAccount')),
                ('club', models.OneToOneField(related_name='club_accounts', to='club.Club')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(primary_key=True, to=settings.AUTH_USER_MODEL, serialize=False)),
                ('account_id', models.CharField(verbose_name='account id', unique=True, max_length=10)),
            ],
            options={
                'verbose_name_plural': 'customers',
                'verbose_name': 'customer',
            },
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(default=None, verbose_name='end date', null=True, blank=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('closed', models.BooleanField(default=False, verbose_name='is closed')),
                ('club_account', models.ForeignKey(related_name='journals', to='accounting.ClubAccount')),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=100)),
                ('journal', models.ForeignKey(related_name='invoices', to='accounting.GeneralJournal')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('code', models.CharField(verbose_name='code', max_length=10)),
                ('purchase_price', accounting.models.CurrencyField(verbose_name='purchase price', decimal_places=2, max_digits=12)),
                ('selling_price', accounting.models.CurrencyField(verbose_name='selling price', decimal_places=2, max_digits=12)),
                ('special_selling_price', accounting.models.CurrencyField(verbose_name='special selling price', decimal_places=2, max_digits=12)),
                ('icon', models.ImageField(blank=True, null=True, upload_to='products')),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('description', models.TextField(blank=True, verbose_name='description', null=True)),
                ('icon', models.ImageField(blank=True, null=True, upload_to='products')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(blank=True, related_name='products', null=True, to='accounting.ProductType'),
        ),
    ]
