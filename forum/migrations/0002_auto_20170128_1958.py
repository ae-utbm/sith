# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forum',
            name='owner_group',
        ),
        migrations.RemoveField(
            model_name='forumtopic',
            name='title',
        ),
    ]
