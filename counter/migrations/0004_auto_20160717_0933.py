# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0003_customer_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='refilling',
            name='bank',
            field=models.CharField(verbose_name='bank', default='other', max_length=255, choices=[('other', 'Autre'), ('la-poste', 'La Poste'), ('credit-agricole', 'Credit Agricole'), ('credit-mutuel', 'Credit Mutuel')]),
        ),
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(verbose_name='payment method', default='cash', max_length=255, choices=[('cheque', 'Chèque'), ('cash', 'Espèce')]),
        ),
    ]
