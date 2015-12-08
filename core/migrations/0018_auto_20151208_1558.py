# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20151203_1530'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (('can_change_prop', "Can change the user's properties (groups, ...)"),), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
