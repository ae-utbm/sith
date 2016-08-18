# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0007_selling_club'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selling',
            name='label',
            field=models.CharField(max_length=64, verbose_name='label'),
        ),
    ]
