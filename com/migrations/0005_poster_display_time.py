# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('com', '0004_auto_20171023_0929'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='display_time',
            field=models.IntegerField(verbose_name='display time', default=30),
        ),
    ]
