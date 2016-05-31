# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0002_refilling_selling'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='amount',
            field=accounting.models.CurrencyField(verbose_name='amount', default=0, decimal_places=2, max_digits=12),
            preserve_default=False,
        ),
    ]
