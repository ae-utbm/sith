# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("forum", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(name="forum", options={"ordering": ["number"]}),
        migrations.AddField(
            model_name="forum",
            name="number",
            field=models.IntegerField(
                verbose_name="number to choose a specific forum ordering", default=1
            ),
        ),
        migrations.AlterField(
            model_name="forum",
            name="edit_groups",
            field=models.ManyToManyField(
                related_name="editable_forums",
                blank=True,
                to="core.Group",
                default=[331],
            ),
        ),
    ]
