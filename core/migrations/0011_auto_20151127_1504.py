# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20151127_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='edit_group',
            field=models.ManyToManyField(to='core.Group', related_name='editable_object', null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='owner_group',
            field=models.ForeignKey(related_name='owned_object', default=1, to='core.Group'),
        ),
        migrations.AddField(
            model_name='page',
            name='view_group',
            field=models.ManyToManyField(to='core.Group', related_name='viewable_object', null=True),
        ),
    ]
