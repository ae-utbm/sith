# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20151119_1533'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='date_of_birth',
            field=models.DateTimeField(default=datetime.datetime(1942, 6, 12, 0, 0, tzinfo=utc), verbose_name='date of birth'),
        ),
    ]
