# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0003_subscription_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='payment_method',
            field=models.CharField(max_length=255, verbose_name='payment method', choices=[('CHEQUE', 'Check'), ('CASH', 'Cash'), ('OTHER', 'Other')]),
        ),
    ]
