# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_auto_20160530_1001'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankaccount',
            name='rib',
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='iban',
            field=models.CharField(blank=True, verbose_name='iban', max_length=255),
        ),
        migrations.AddField(
            model_name='generaljournal',
            name='amount',
            field=accounting.models.CurrencyField(default=0, max_digits=12, decimal_places=2, verbose_name='amount'),
            preserve_default=False,
        ),
    ]
