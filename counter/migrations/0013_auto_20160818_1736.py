# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0012_selling_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selling',
            name='payment_method',
            field=models.CharField(max_length=255, default='SITH_ACCOUNT', verbose_name='payment method', choices=[('SITH_ACCOUNT', 'Sith account'), ('CARD', 'Credit card')]),
        ),
    ]
