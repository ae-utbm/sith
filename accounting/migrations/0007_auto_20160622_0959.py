# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0006_operation_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='cheque_number',
            field=models.IntegerField(verbose_name='cheque number', default=-1),
        ),
    ]
