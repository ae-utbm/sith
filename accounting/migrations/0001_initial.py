# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('club', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountingType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=16, verbose_name='code')),
                ('label', models.CharField(max_length=60, verbose_name='label')),
                ('movement_type', models.CharField(max_length=12, verbose_name='movement type', choices=[('credit', 'Credit'), ('debit', 'Debit'), ('neutral', 'Neutral')])),
            ],
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('rib', models.CharField(max_length=255, verbose_name='rib', blank=True)),
                ('number', models.CharField(max_length=255, verbose_name='account number', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ClubAccount',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('bank_account', models.ForeignKey(related_name='club_accounts', to='accounting.BankAccount')),
                ('club', models.OneToOneField(related_name='club_accounts', to='club.Club')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, primary_key=True, serialize=False)),
                ('account_id', models.CharField(max_length=10, verbose_name='account id', unique=True)),
            ],
            options={
                'verbose_name_plural': 'customers',
                'verbose_name': 'customer',
            },
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(null=True, default=None, verbose_name='end date', blank=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('closed', models.BooleanField(default=False, verbose_name='is closed')),
                ('club_account', models.ForeignKey(related_name='journals', to='accounting.ClubAccount')),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='date')),
                ('remark', models.TextField(max_length=255, verbose_name='remark')),
                ('mode', models.CharField(max_length=255, verbose_name='payment method', choices=[('cheque', 'Chèque'), ('cash', 'Espèce'), ('transfert', 'Virement'), ('card', 'Carte banquaire')])),
                ('cheque_number', models.IntegerField(verbose_name='cheque number')),
                ('invoice', models.FileField(null=True, upload_to='invoices', blank=True)),
                ('done', models.BooleanField(default=False, verbose_name='is done')),
                ('journal', models.ForeignKey(related_name='invoices', to='accounting.GeneralJournal')),
                ('type', models.ForeignKey(related_name='operations', to='accounting.AccountingType')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('code', models.CharField(max_length=10, verbose_name='code')),
                ('purchase_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='purchase price')),
                ('selling_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='selling price')),
                ('special_selling_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='special selling price')),
                ('icon', models.ImageField(null=True, upload_to='products', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('icon', models.ImageField(null=True, upload_to='products', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(null=True, to='accounting.ProductType', related_name='products', blank=True),
        ),
    ]
