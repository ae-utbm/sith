# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_auto_20160617_1520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaljournal',
            name='amount',
            field=accounting.models.CurrencyField(max_digits=12, verbose_name='amount', default=0, decimal_places=2),
        ),
    ]
