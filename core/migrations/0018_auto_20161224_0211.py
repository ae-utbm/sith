# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0017_auto_20161220_1626")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(
                choices=[
                    ("NEWS_MODERATION", "A fresh new to be moderated"),
                    ("FILE_MODERATION", "New files to be moderated"),
                    ("SAS_MODERATION", "New pictures/album to be moderated in the SAS"),
                    ("NEW_PICTURES", "You've been identified on some pictures"),
                    ("REFILLING", "You just refilled of %s €"),
                    ("SELLING", "You just bought %s"),
                    ("GENERIC", "You have a notification"),
                ],
                default="GENERIC",
                max_length=32,
                verbose_name="type",
            ),
        )
    ]
