# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("election", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="election",
            name="archived",
            field=models.BooleanField(verbose_name="archived", default=False),
        )
    ]
