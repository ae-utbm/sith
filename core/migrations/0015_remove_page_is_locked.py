# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_remove_page_revision'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='is_locked',
        ),
    ]
