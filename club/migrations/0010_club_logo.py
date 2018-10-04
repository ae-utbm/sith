# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("club", "0009_auto_20170822_2232")]

    operations = [
        migrations.AddField(
            model_name="club",
            name="logo",
            field=models.ImageField(
                null=True, upload_to="club_logos", blank=True, verbose_name="logo"
            ),
        )
    ]
