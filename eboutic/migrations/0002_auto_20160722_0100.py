# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eboutic', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='products',
        ),
        migrations.AddField(
            model_name='invoice',
            name='validated',
            field=models.BooleanField(default=False, verbose_name='validated'),
        ),
    ]
