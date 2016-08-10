# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
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
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(verbose_name='code', max_length=16)),
                ('label', models.CharField(verbose_name='label', max_length=60)),
                ('movement_type', models.CharField(verbose_name='movement type', choices=[('credit', 'Credit'), ('debit', 'Debit'), ('neutral', 'Neutral')], max_length=12)),
            ],
            options={
                'verbose_name': 'accounting type',
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('iban', models.CharField(blank=True, verbose_name='iban', max_length=255)),
                ('number', models.CharField(blank=True, verbose_name='account number', max_length=255)),
                ('club', models.ForeignKey(related_name='bank_accounts', to='club.Club')),
            ],
        ),
        migrations.CreateModel(
            name='ClubAccount',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('bank_account', models.ForeignKey(related_name='club_accounts', to='accounting.BankAccount')),
                ('club', models.OneToOneField(related_name='club_account', to='club.Club')),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=60)),
            ],
            options={
                'verbose_name': 'company',
            },
        ),
        migrations.CreateModel(
            name='GeneralJournal',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(default=None, null=True, verbose_name='end date', blank=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('closed', models.BooleanField(default=False, verbose_name='is closed')),
                ('amount', accounting.models.CurrencyField(default=0, decimal_places=2, max_digits=12, verbose_name='amount')),
                ('effective_amount', accounting.models.CurrencyField(default=0, decimal_places=2, max_digits=12, verbose_name='effective_amount')),
                ('club_account', models.ForeignKey(related_name='journals', to='accounting.ClubAccount')),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('number', models.IntegerField(verbose_name='number')),
                ('amount', accounting.models.CurrencyField(decimal_places=2, max_digits=12, verbose_name='amount')),
                ('date', models.DateField(verbose_name='date')),
                ('label', models.CharField(verbose_name='label', max_length=50)),
                ('remark', models.TextField(verbose_name='remark', max_length=255)),
                ('mode', models.CharField(verbose_name='payment method', choices=[('CHEQUE', 'Check'), ('CASH', 'Cash'), ('TRANSFert', 'Transfert'), ('CARD', 'Credit card')], max_length=255)),
                ('cheque_number', models.IntegerField(default=-1, verbose_name='cheque number')),
                ('done', models.BooleanField(default=False, verbose_name='is done')),
                ('target_type', models.CharField(verbose_name='target type', choices=[('USER', 'User'), ('CLUB', 'Club'), ('ACCOUNT', 'Account'), ('COMPANY', 'Company'), ('OTHER', 'Other')], max_length=10)),
                ('target_id', models.IntegerField(null=True, verbose_name='target id', blank=True)),
                ('target_label', models.CharField(default='', blank=True, verbose_name='target label', max_length=32)),
                ('accounting_type', models.ForeignKey(verbose_name='accounting type', related_name='operations', to='accounting.AccountingType')),
                ('invoice', models.ForeignKey(verbose_name='invoice', related_name='operations', blank=True, null=True, to='core.SithFile')),
                ('journal', models.ForeignKey(related_name='operations', to='accounting.GeneralJournal')),
            ],
            options={
                'ordering': ['-number'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='operation',
            unique_together=set([('number', 'journal')]),
        ),
    ]
