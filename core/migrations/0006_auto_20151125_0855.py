# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20151124_1219'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'permissions': (('can_view', 'Can view the page'),)},
        ),
    ]
