# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eboutic', '0002_auto_20160818_1635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='payment_method',
            field=models.CharField(verbose_name='payment method', max_length=20, choices=[('CARD', 'Credit card'), ('SITH_ACCOUNT', 'Sith account')]),
        ),
    ]
