# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20161212_1922'),
        ('election', '0003_auto_20161219_1832'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='election',
            name='candidature_group',
        ),
        migrations.RemoveField(
            model_name='election',
            name='vote_group',
        ),
        migrations.AddField(
            model_name='election',
            name='candidature_groups',
            field=models.ManyToManyField(to='core.Group', verbose_name='candidature group', related_name='candidate_elections', blank=True),
        ),
        migrations.AddField(
            model_name='election',
            name='vote_groups',
            field=models.ManyToManyField(to='core.Group', verbose_name='vote group', related_name='votable_elections', blank=True),
        ),
        migrations.AlterField(
            model_name='election',
            name='edit_groups',
            field=models.ManyToManyField(to='core.Group', verbose_name='edit group', related_name='editable_elections', blank=True),
        ),
        migrations.AlterField(
            model_name='election',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', verbose_name='view group', related_name='viewable_elections', blank=True),
        ),
    ]
