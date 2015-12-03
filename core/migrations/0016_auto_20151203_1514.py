# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_remove_page_is_locked'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='edit_group',
            field=models.ManyToManyField(to='core.Group', related_name='editable_user'),
        ),
        migrations.AddField(
            model_name='user',
            name='owner_group',
            field=models.ForeignKey(related_name='owned_user', to='core.Group', default=1),
        ),
        migrations.AddField(
            model_name='user',
            name='view_group',
            field=models.ManyToManyField(to='core.Group', related_name='viewable_user'),
        ),
        migrations.AlterField(
            model_name='page',
            name='edit_group',
            field=models.ManyToManyField(to='core.Group', related_name='editable_page'),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner_group',
            field=models.ForeignKey(related_name='owned_page', to='core.Group', default=1),
        ),
        migrations.AlterField(
            model_name='page',
            name='view_group',
            field=models.ManyToManyField(to='core.Group', related_name='viewable_page'),
        ),
    ]
