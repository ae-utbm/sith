# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('club', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='edit_groups',
            field=models.ManyToManyField(to='core.Group', blank=True, related_name='editable_club'),
        ),
        migrations.AddField(
            model_name='club',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', blank=True, related_name='viewable_club'),
        ),
    ]
