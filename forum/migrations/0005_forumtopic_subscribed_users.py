# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forum", "0004_auto_20170531_1949"),
    ]

    operations = [
        migrations.AddField(
            model_name="forumtopic",
            name="subscribed_users",
            field=models.ManyToManyField(
                verbose_name="subscribed users",
                related_name="favorite_topics",
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
