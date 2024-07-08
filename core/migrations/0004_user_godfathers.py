# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0003_auto_20160902_1914")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="godfathers",
            field=models.ManyToManyField(
                to=settings.AUTH_USER_MODEL, related_name="godchildren", blank=True
            ),
        )
    ]
