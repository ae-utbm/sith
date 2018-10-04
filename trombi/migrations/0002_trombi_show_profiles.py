# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("trombi", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="trombi",
            name="show_profiles",
            field=models.BooleanField(
                default=True, verbose_name="show users profiles to each other"
            ),
        )
    ]
