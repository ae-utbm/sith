# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0008_auto_20160818_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(verbose_name='payment method', default='CASH', choices=[('CHECK', 'Check'), ('CASH', 'Cash'), ('EBOUTIC', 'Eboutic')], max_length=255),
        ),
    ]
