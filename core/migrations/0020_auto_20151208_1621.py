# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20151208_1604'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name_plural': 'users', 'permissions': (('change_prop_user', "Can change the user's properties (groups, ...)"),), 'verbose_name': 'user'},
        ),
    ]
