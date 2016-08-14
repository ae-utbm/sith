# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='mode',
            field=models.CharField(verbose_name='payment method', max_length=255, choices=[('CHECK', 'Check'), ('CASH', 'Cash'), ('TRANSFERT', 'Transfert'), ('CARD', 'Credit card')]),
        ),
    ]
