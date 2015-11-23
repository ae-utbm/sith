# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20151123_0902'),
    ]

    operations = [
        migrations.RenameField(
            model_name='page',
            old_name='name',
            new_name='full_name',
        ),
    ]
