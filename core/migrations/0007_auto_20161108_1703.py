# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sithfile',
            name='is_authorized',
        ),
        migrations.AddField(
            model_name='sithfile',
            name='is_moderated',
            field=models.BooleanField(verbose_name='is moderated', default=False),
        ),
    ]
