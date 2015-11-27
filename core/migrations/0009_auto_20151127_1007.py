# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20151127_1007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='edit_group',
        ),
        migrations.AddField(
            model_name='page',
            name='edit_group',
            field=models.ManyToManyField(to='core.Group', related_name='editable_pages', default=1),
        ),
    ]
