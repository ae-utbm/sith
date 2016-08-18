# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0009_auto_20160818_1709'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(default='CASH', max_length=255, verbose_name='payment method', choices=[('CHECK', 'Check'), ('CASH', 'Cash'), ('CARD', 'Credit card')]),
        ),
    ]
