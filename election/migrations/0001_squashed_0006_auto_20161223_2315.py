# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    replaces = [('election', '0001_initial'), ('election', '0002_role_max_choice'), ('election', '0003_auto_20161219_1832'), ('election', '0004_auto_20161219_2302'), ('election', '0005_auto_20161223_2240'), ('election', '0006_auto_20161223_2315')]

    dependencies = [
        ('core', '0016_auto_20161212_1922'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidature',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('program', models.TextField(null=True, verbose_name='description', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('start_candidature', models.DateTimeField(verbose_name='start candidature')),
                ('end_candidature', models.DateTimeField(verbose_name='end candidature')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(verbose_name='end date')),
            ],
        ),
        migrations.CreateModel(
            name='ElectionList',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('election', models.ForeignKey(related_name='election_lists', verbose_name='election', to='election.Election')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('election', models.ForeignKey(related_name='role', verbose_name='election', to='election.Election')),
                ('has_voted', models.ManyToManyField(related_name='has_voted', verbose_name='has voted', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('candidature', models.ManyToManyField(related_name='votes', verbose_name='candidature', to='election.Candidature')),
                ('role', models.ForeignKey(related_name='votes', verbose_name='role', to='election.Role')),
            ],
        ),
        migrations.AddField(
            model_name='candidature',
            name='election_list',
            field=models.ForeignKey(related_name='candidatures', verbose_name='election_list', to='election.ElectionList'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='role',
            field=models.ForeignKey(related_name='candidatures', verbose_name='role', to='election.Role'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='user',
            field=models.ForeignKey(related_name='candidates', verbose_name='user', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AddField(
            model_name='role',
            name='max_choice',
            field=models.IntegerField(default=1, verbose_name='max choice'),
        ),
        migrations.AddField(
            model_name='election',
            name='edit_groups',
            field=models.ManyToManyField(related_name='editable_elections', verbose_name='edit groups', blank=True, to='core.Group'),
        ),
        migrations.AddField(
            model_name='election',
            name='view_groups',
            field=models.ManyToManyField(related_name='viewable_elections', verbose_name='view groups', blank=True, to='core.Group'),
        ),
        migrations.AddField(
            model_name='election',
            name='candidature_groups',
            field=models.ManyToManyField(related_name='candidate_elections', verbose_name='candidature groups', blank=True, to='core.Group'),
        ),
        migrations.AddField(
            model_name='election',
            name='vote_groups',
            field=models.ManyToManyField(related_name='votable_elections', verbose_name='vote groups', blank=True, to='core.Group'),
        ),
        migrations.AlterField(
            model_name='role',
            name='election',
            field=models.ForeignKey(related_name='roles', verbose_name='election', to='election.Election'),
        ),
        migrations.RemoveField(
            model_name='role',
            name='has_voted',
        ),
        migrations.AddField(
            model_name='election',
            name='voters',
            field=models.ManyToManyField(related_name='has_voted', verbose_name='has voted', to=settings.AUTH_USER_MODEL),
        ),
    ]
