# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20151208_1558'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (('change_prop', "Can change the user's properties (groups, ...)"),), 'verbose_name_plural': 'users', 'verbose_name': 'user'},
        ),
    ]
