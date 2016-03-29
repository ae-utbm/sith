# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='counter',
            name='type',
            field=models.CharField(max_length=255, default='BAR', verbose_name='subscription type', choices=[('BAR', 'Bar'), ('OFFICE', 'Office')]),
            preserve_default=False,
        ),
    ]
