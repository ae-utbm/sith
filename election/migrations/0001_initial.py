# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidature',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('program', models.TextField(blank=True, null=True, verbose_name='description')),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('start_candidature', models.DateTimeField(verbose_name='start candidature')),
                ('end_candidature', models.DateTimeField(verbose_name='end candidature')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(verbose_name='end date')),
            ],
        ),
        migrations.CreateModel(
            name='ElectionList',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('election', models.ForeignKey(related_name='election_list', verbose_name='election', to='election.Election')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('election', models.ForeignKey(related_name='role', verbose_name='election', to='election.Election')),
                ('has_voted', models.ManyToManyField(related_name='has_voted', to=settings.AUTH_USER_MODEL, verbose_name='has voted')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('candidature', models.ManyToManyField(related_name='vote', to='election.Candidature', verbose_name='candidature')),
                ('role', models.ForeignKey(related_name='vote', verbose_name='role', to='election.Role')),
            ],
        ),
        migrations.AddField(
            model_name='candidature',
            name='election_list',
            field=models.ForeignKey(related_name='candidature', verbose_name='election_list', to='election.ElectionList'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='role',
            field=models.ForeignKey(related_name='candidature', verbose_name='role', to='election.Role'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='candidate', blank=True, verbose_name='user'),
        ),
    ]
