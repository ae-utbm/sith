# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("club", "0004_auto_20160915_1057")]

    operations = [
        migrations.AlterField(
            model_name="club",
            name="home",
            field=models.OneToOneField(
                related_name="home_of_club",
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="home",
                null=True,
                to="core.SithFile",
            ),
        )
    ]
