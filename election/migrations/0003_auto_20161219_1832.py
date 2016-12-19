# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20161212_1922'),
        ('election', '0002_role_max_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='candidature_group',
            field=models.ManyToManyField(related_name='candidate_election', blank=True, verbose_name='candidature group', to='core.Group'),
        ),
        migrations.AddField(
            model_name='election',
            name='edit_groups',
            field=models.ManyToManyField(related_name='editable_election', blank=True, verbose_name='edit group', to='core.Group'),
        ),
        migrations.AddField(
            model_name='election',
            name='view_groups',
            field=models.ManyToManyField(related_name='viewable_election', blank=True, verbose_name='view group', to='core.Group'),
        ),
        migrations.AddField(
            model_name='election',
            name='vote_group',
            field=models.ManyToManyField(related_name='votable_election', blank=True, verbose_name='vote group', to='core.Group'),
        ),
    ]
