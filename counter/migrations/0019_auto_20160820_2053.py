# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0018_auto_20160820_2051'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='buying_group',
            new_name='buying_groups',
        ),
    ]
