# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import forum.models


class Migration(migrations.Migration):

    dependencies = [("forum", "0005_forumtopic_subscribed_users")]

    operations = [
        migrations.AlterField(
            model_name="forum",
            name="edit_groups",
            field=models.ManyToManyField(
                blank=True,
                default=forum.models.Forum.get_default_edit_group,
                related_name="editable_forums",
                to="core.Group",
            ),
        ),
        migrations.AlterField(
            model_name="forum",
            name="view_groups",
            field=models.ManyToManyField(
                blank=True,
                default=forum.models.Forum.get_default_view_group,
                related_name="viewable_forums",
                to="core.Group",
            ),
        ),
    ]
