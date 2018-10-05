# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [("counter", "0002_auto_20160826_1342")]

    operations = [
        migrations.AddField(
            model_name="permanency",
            name="activity",
            field=models.DateTimeField(
                verbose_name="activity time",
                auto_now=True,
                default=datetime.datetime(2016, 8, 26, 17, 5, 31, 202824, tzinfo=utc),
            ),
            preserve_default=False,
        )
    ]
