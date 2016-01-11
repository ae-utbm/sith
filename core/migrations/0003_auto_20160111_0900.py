# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20151215_0827'),
    ]

    operations = [
        migrations.RenameField(
            model_name='page',
            old_name='full_name',
            new_name='_full_name',
        ),
    ]
