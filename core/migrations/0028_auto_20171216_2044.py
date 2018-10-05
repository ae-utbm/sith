# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0027_gift")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(
                default="GENERIC",
                verbose_name="type",
                max_length=32,
                choices=[
                    ("POSTER_MODERATION", "A new poster needs to be moderated"),
                    ("MAILING_MODERATION", "A new mailing list needs to be moderated"),
                    ("NEWS_MODERATION", "There are %s fresh news to be moderated"),
                    ("FILE_MODERATION", "New files to be moderated"),
                    (
                        "SAS_MODERATION",
                        "There are %s pictures to be moderated in the SAS",
                    ),
                    ("NEW_PICTURES", "You've been identified on some pictures"),
                    ("REFILLING", "You just refilled of %s €"),
                    ("SELLING", "You just bought %s"),
                    ("GENERIC", "You have a notification"),
                ],
            ),
        )
    ]
