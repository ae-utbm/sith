# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_auto_20160818_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='selling',
            name='payment_method',
            field=models.CharField(default='SITH_ACCOUNT', max_length=255, verbose_name='payment method', choices=[('SITH_ACCOUNT', 'Compte AE'), ('CARD', 'Credit card')]),
        ),
    ]
