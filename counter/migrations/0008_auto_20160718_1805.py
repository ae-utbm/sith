# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0007_permanency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(max_length=255, verbose_name='payment method', default='cash', choices=[('cheque', 'Check'), ('cash', 'Cash')]),
        ),
    ]
