# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0008_auto_20160622_1005'),
    ]

    operations = [
        migrations.AddField(
            model_name='operation',
            name='label',
            field=models.CharField(verbose_name='label', default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='operation',
            name='type',
            field=models.CharField(verbose_name='operation type', choices=[('debit', 'Debit'), ('credit', 'Credit')], max_length=8),
        ),
    ]
