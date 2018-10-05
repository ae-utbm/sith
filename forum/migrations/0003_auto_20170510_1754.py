# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("forum", "0002_auto_20170312_1753")]

    operations = [
        migrations.AlterField(
            model_name="forum",
            name="edit_groups",
            field=models.ManyToManyField(
                blank=True, default=[4], related_name="editable_forums", to="core.Group"
            ),
        )
    ]
