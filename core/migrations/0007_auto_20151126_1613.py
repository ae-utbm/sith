# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('core', '0006_auto_20151125_0855'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_ptr', models.OneToOneField(auto_created=True, to='auth.Group', primary_key=True, serialize=False, parent_link=True)),
            ],
            bases=('auth.group',),
        ),
        migrations.AlterField(
            model_name='page',
            name='edit_group',
            field=models.ForeignKey(default=1, to='core.Group', related_name='editable_pages'),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner_group',
            field=models.ForeignKey(default=1, to='core.Group', related_name='owned_pages'),
        ),
        migrations.AlterField(
            model_name='page',
            name='view_group',
            field=models.ForeignKey(default=1, to='core.Group', related_name='viewable_pages'),
        ),
    ]
