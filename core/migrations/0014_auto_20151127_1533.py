# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20151127_1521'),
    ]

    operations = [
        migrations.RenameField(
            model_name='page',
            old_name='last_revision',
            new_name='revision',
        ),
    ]
