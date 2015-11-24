# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20151124_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='edit_group',
            field=models.ForeignKey(related_name='editable_pages', to='auth.Group', default=1),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner_group',
            field=models.ForeignKey(related_name='owned_pages', to='auth.Group', default=1),
        ),
        migrations.AlterField(
            model_name='page',
            name='view_group',
            field=models.ForeignKey(related_name='viewable_pages', to='auth.Group', default=1),
        ),
    ]
