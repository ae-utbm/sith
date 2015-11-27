# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20151127_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='edit_group',
            field=models.ManyToManyField(related_name='editable_object', to='core.Group'),
        ),
        migrations.AlterField(
            model_name='page',
            name='view_group',
            field=models.ManyToManyField(related_name='viewable_object', to='core.Group'),
        ),
    ]
