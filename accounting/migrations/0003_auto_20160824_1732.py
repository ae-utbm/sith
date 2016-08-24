# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_auto_20160814_1634'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimplifiedAccountingType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('label', models.CharField(max_length=128, verbose_name='label')),
            ],
            options={
                'verbose_name': 'simplified type',
            },
        ),
        migrations.RemoveField(
            model_name='operation',
            name='label',
        ),
        migrations.AddField(
            model_name='operation',
            name='linked_operation',
            field=models.OneToOneField(to='accounting.Operation', default=None, null=True, blank=True, verbose_name='linked operation', related_name='operation_linked_to'),
        ),
        migrations.AlterField(
            model_name='accountingtype',
            name='code',
            field=models.CharField(max_length=16, verbose_name='code', validators=[django.core.validators.RegexValidator('^[0-9]*$', 'An accounting type code contains only numbers')]),
        ),
        migrations.AlterField(
            model_name='accountingtype',
            name='label',
            field=models.CharField(max_length=128, verbose_name='label'),
        ),
        migrations.AlterField(
            model_name='accountingtype',
            name='movement_type',
            field=models.CharField(max_length=12, verbose_name='movement type', choices=[('CREDIT', 'Credit'), ('DEBIT', 'Debit'), ('NEUTRAL', 'Neutral')]),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='club',
            field=models.ForeignKey(related_name='bank_accounts', verbose_name='club', to='club.Club'),
        ),
        migrations.AlterField(
            model_name='clubaccount',
            name='bank_account',
            field=models.ForeignKey(related_name='club_accounts', verbose_name='bank account', to='accounting.BankAccount'),
        ),
        migrations.AlterField(
            model_name='clubaccount',
            name='club',
            field=models.ForeignKey(related_name='club_account', verbose_name='club', to='club.Club'),
        ),
        migrations.AlterField(
            model_name='generaljournal',
            name='club_account',
            field=models.ForeignKey(related_name='journals', verbose_name='club account', to='accounting.ClubAccount'),
        ),
        migrations.AlterField(
            model_name='generaljournal',
            name='name',
            field=models.CharField(max_length=40, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='accounting_type',
            field=models.ForeignKey(related_name='operations', null=True, blank=True, verbose_name='accounting type', to='accounting.AccountingType'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='cheque_number',
            field=models.CharField(verbose_name='cheque number', null=True, max_length=32, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='operation',
            name='journal',
            field=models.ForeignKey(related_name='operations', verbose_name='journal', to='accounting.GeneralJournal'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='remark',
            field=models.CharField(max_length=128, verbose_name='comment'),
        ),
        migrations.AddField(
            model_name='simplifiedaccountingtype',
            name='accounting_type',
            field=models.ForeignKey(related_name='simplified_types', verbose_name='simplified accounting types', to='accounting.AccountingType'),
        ),
        migrations.AddField(
            model_name='operation',
            name='simpleaccounting_type',
            field=models.ForeignKey(related_name='operations', null=True, blank=True, verbose_name='simple type', to='accounting.SimplifiedAccountingType'),
        ),
    ]
