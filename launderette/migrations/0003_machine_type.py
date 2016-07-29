# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0002_auto_20160729_0138'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='type',
            field=models.CharField(choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')], max_length=10, default='WASHING', verbose_name='type'),
            preserve_default=False,
        ),
    ]
