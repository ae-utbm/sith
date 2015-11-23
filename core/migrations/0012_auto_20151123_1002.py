# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_page_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='children',
        ),
        migrations.AddField(
            model_name='page',
            name='parent',
            field=models.ForeignKey(null=True, related_name='children', to='core.Page'),
        ),
    ]
