# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0009_eticket")]

    operations = [
        migrations.AddField(
            model_name="eticket",
            name="event_date",
            field=models.DateField(blank=True, verbose_name="event date", null=True),
        ),
        migrations.AddField(
            model_name="eticket",
            name="event_title",
            field=models.CharField(
                blank=True, max_length=64, verbose_name="event title", null=True
            ),
        ),
    ]
