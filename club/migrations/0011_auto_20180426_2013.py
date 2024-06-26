# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import club.models


class Migration(migrations.Migration):
    dependencies = [("club", "0010_auto_20170912_2028")]

    operations = [
        migrations.AlterField(
            model_name="club",
            name="owner_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=club.models.Club.get_default_owner_group,
                related_name="owned_club",
                to="core.Group",
            ),
        )
    ]
