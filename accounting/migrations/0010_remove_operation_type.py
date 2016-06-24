# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0009_auto_20160622_1030'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='operation',
            name='type',
        ),
    ]
