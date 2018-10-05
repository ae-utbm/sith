# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [("club", "0003_auto_20160902_2042")]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                verbose_name="user",
                related_name="memberships",
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
