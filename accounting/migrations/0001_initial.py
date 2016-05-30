# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccountingType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('code', models.CharField(max_length=16, verbose_name='code')),
                ('label', models.CharField(max_length=60, verbose_name='label')),
                ('movement_type', models.CharField(choices=[('credit', 'Credit'), ('debit', 'Debit'), ('neutral', 'Neutral')], max_length=12, verbose_name='movement type')),
            ],
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('rib', models.CharField(blank=True, max_length=255, verbose_name='rib')),
                ('number', models.CharField(blank=True, max_length=255, verbose_name='account number')),
            ],
        ),
        migrations.CreateModel(
            name='ClubAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('bank_account', models.ForeignKey(to='accounting.BankAccount', related_name='club_accounts')),
            ],
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(default=None, blank=True, verbose_name='end date', null=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('closed', models.BooleanField(verbose_name='is closed', default=False)),
                ('club_account', models.ForeignKey(to='accounting.ClubAccount', related_name='journals')),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('amount', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='amount')),
                ('date', models.DateField(verbose_name='date')),
                ('remark', models.TextField(max_length=255, verbose_name='remark')),
                ('mode', models.CharField(choices=[('cheque', 'Chèque'), ('cash', 'Espèce'), ('transfert', 'Virement'), ('card', 'Carte banquaire')], max_length=255, verbose_name='payment method')),
                ('cheque_number', models.IntegerField(verbose_name='cheque number')),
                ('invoice', models.FileField(blank=True, upload_to='invoices', null=True)),
                ('done', models.BooleanField(verbose_name='is done', default=False)),
                ('journal', models.ForeignKey(to='accounting.GeneralJournal', related_name='operations')),
                ('type', models.ForeignKey(to='accounting.AccountingType', related_name='operations')),
            ],
        ),
    ]
