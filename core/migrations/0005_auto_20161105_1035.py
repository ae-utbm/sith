# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [("core", "0004_user_godfathers")]

    operations = [
        migrations.AddField(
            model_name="page",
            name="lock_timeout",
            field=models.DateTimeField(
                verbose_name="lock_timeout", null=True, blank=True, default=None
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="lock_user",
            field=models.ForeignKey(
                verbose_name="lock user",
                default=None,
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
                related_name="locked_pages",
            ),
        ),
    ]
