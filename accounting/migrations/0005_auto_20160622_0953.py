# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0004_auto_20160620_1307'),
    ]

    operations = [
        migrations.RenameField(
            model_name='operation',
            old_name='type',
            new_name='accounting_type',
        ),
        migrations.AddField(
            model_name='generaljournal',
            name='effective_amount',
            field=accounting.models.CurrencyField(default=0, decimal_places=2, verbose_name='effective_amount', max_digits=12),
        ),
    ]
