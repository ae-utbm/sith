# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0013_auto_20160818_1736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='date',
            field=models.DateTimeField(verbose_name='date'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='date',
            field=models.DateTimeField(verbose_name='date'),
        ),
    ]
