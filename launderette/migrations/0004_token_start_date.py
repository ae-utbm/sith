# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0003_machine_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 29, 10, 46, 13, 675691, tzinfo=utc), verbose_name='start date'),
            preserve_default=False,
        ),
    ]
