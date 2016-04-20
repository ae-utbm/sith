# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='number',
            field=models.CharField(max_length=255, blank=True, verbose_name='account number'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='rib',
            field=models.CharField(max_length=255, blank=True, verbose_name='rib'),
        ),
    ]
