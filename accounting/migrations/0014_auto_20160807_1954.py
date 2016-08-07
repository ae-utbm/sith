# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0013_auto_20160807_1923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='mode',
            field=models.CharField(max_length=255, verbose_name='payment method', choices=[('CHEQUE', 'Check'), ('CASH', 'Cash'), ('TRANSFert', 'Transfert'), ('CARD', 'Credit card')]),
        ),
    ]
