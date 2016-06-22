# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0005_auto_20160622_0953'),
    ]

    operations = [
        migrations.AddField(
            model_name='operation',
            name='type',
            field=models.CharField(verbose_name='operation type', choices=[('DEBIT', 'Debit'), ('CREDIT', 'Credit')], max_length=10, default='DEBIT'),
            preserve_default=False,
        ),
    ]
