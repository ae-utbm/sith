# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20151202_0814'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='revision',
        ),
    ]
