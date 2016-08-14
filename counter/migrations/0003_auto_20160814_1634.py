# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0002_auto_20160810_1348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(verbose_name='payment method', default='cash', max_length=255, choices=[('CHECK', 'Check'), ('CASH', 'Cash')]),
        ),
    ]
