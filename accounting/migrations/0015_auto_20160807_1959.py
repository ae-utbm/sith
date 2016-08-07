# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0014_auto_20160807_1954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='accounting_type',
            field=models.ForeignKey(related_name='operations', verbose_name='accounting type', to='accounting.AccountingType'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='invoice',
            field=models.FileField(upload_to='invoices', verbose_name='invoice', null=True, blank=True),
        ),
    ]
