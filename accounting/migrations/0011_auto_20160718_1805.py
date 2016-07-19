# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0010_remove_operation_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='mode',
            field=models.CharField(max_length=255, verbose_name='payment method', choices=[('cheque', 'Check'), ('cash', 'Cash'), ('transfert', 'Transfert'), ('card', 'Credit card')]),
        ),
    ]
