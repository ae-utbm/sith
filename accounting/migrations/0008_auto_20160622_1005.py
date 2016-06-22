# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0007_auto_20160622_0959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='type',
            field=models.CharField(verbose_name='operation type', choices=[('debit', 'Debit'), ('credit', 'Credit')], max_length=10),
        ),
    ]
