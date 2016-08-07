# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0014_auto_20160804_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='bank',
            field=models.CharField(max_length=255, verbose_name='bank', choices=[('OTHER', 'Autre'), ('LA-POSTE', 'La Poste'), ('CREDIT-AGRICOLE', 'Credit Agricole'), ('CREDIT-MUTUEL', 'Credit Mutuel')], default='other'),
        ),
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(max_length=255, verbose_name='payment method', choices=[('CHEQUE', 'Check'), ('CASH', 'Cash')], default='cash'),
        ),
    ]
