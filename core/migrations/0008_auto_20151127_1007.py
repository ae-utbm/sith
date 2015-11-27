# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20151126_1613'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='view_group',
        ),
        migrations.AddField(
            model_name='page',
            name='view_group',
            field=models.ManyToManyField(default=1, to='core.Group', related_name='viewable_pages'),
        ),
    ]
