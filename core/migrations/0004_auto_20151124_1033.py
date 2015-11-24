# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('core', '0003_auto_20151124_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='edit_group',
            field=models.ForeignKey(null=True, to='auth.Group', related_name='editable_pages'),
        ),
        migrations.AddField(
            model_name='page',
            name='owner_group',
            field=models.ForeignKey(null=True, to='auth.Group', related_name='owned_pages'),
        ),
        migrations.AddField(
            model_name='page',
            name='view_group',
            field=models.ForeignKey(null=True, to='auth.Group', related_name='viewable_pages'),
        ),
    ]
