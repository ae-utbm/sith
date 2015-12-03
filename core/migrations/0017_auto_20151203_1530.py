# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20151203_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='edit_group',
            field=models.ManyToManyField(blank=True, related_name='editable_page', to='core.Group'),
        ),
        migrations.AlterField(
            model_name='page',
            name='view_group',
            field=models.ManyToManyField(blank=True, related_name='viewable_page', to='core.Group'),
        ),
        migrations.AlterField(
            model_name='user',
            name='edit_group',
            field=models.ManyToManyField(blank=True, related_name='editable_user', to='core.Group'),
        ),
        migrations.AlterField(
            model_name='user',
            name='view_group',
            field=models.ManyToManyField(blank=True, related_name='viewable_user', to='core.Group'),
        ),
    ]
