# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20151127_1007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='edit_group',
        ),
        migrations.RemoveField(
            model_name='page',
            name='owner_group',
        ),
        migrations.RemoveField(
            model_name='page',
            name='view_group',
        ),
    ]
