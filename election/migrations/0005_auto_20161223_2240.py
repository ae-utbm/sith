# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0004_auto_20161219_2302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidature',
            name='election_list',
            field=models.ForeignKey(related_name='candidatures', to='election.ElectionList', verbose_name='election_list'),
        ),
        migrations.AlterField(
            model_name='candidature',
            name='role',
            field=models.ForeignKey(related_name='candidatures', to='election.Role', verbose_name='role'),
        ),
        migrations.AlterField(
            model_name='candidature',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL, related_name='candidates', blank=True),
        ),
        migrations.AlterField(
            model_name='election',
            name='candidature_groups',
            field=models.ManyToManyField(to='core.Group', related_name='candidate_elections', blank=True, verbose_name='candidature groups'),
        ),
        migrations.AlterField(
            model_name='election',
            name='edit_groups',
            field=models.ManyToManyField(to='core.Group', related_name='editable_elections', blank=True, verbose_name='edit groups'),
        ),
        migrations.AlterField(
            model_name='election',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', related_name='viewable_elections', blank=True, verbose_name='view groups'),
        ),
        migrations.AlterField(
            model_name='election',
            name='vote_groups',
            field=models.ManyToManyField(to='core.Group', related_name='votable_elections', blank=True, verbose_name='vote groups'),
        ),
        migrations.AlterField(
            model_name='electionlist',
            name='election',
            field=models.ForeignKey(related_name='election_lists', to='election.Election', verbose_name='election'),
        ),
        migrations.AlterField(
            model_name='role',
            name='election',
            field=models.ForeignKey(related_name='roles', to='election.Election', verbose_name='election'),
        ),
        migrations.AlterField(
            model_name='vote',
            name='candidature',
            field=models.ManyToManyField(to='election.Candidature', related_name='votes', verbose_name='candidature'),
        ),
        migrations.AlterField(
            model_name='vote',
            name='role',
            field=models.ForeignKey(related_name='votes', to='election.Role', verbose_name='role'),
        ),
    ]
