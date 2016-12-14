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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('program', models.TextField(null=True, verbose_name='description', blank=True)),
                ('has_voted', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='has_voted', verbose_name='has_voted')),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('start_candidature', models.DateTimeField(verbose_name='start candidature')),
                ('end_candidature', models.DateTimeField(verbose_name='end candidature')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(verbose_name='end date')),
            ],
        ),
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('election', models.ForeignKey(to='election.Election', related_name='list', verbose_name='election')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('election', models.ForeignKey(to='election.Election', related_name='role', verbose_name='election')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('candidature', models.ManyToManyField(to='election.Candidature', related_name='vote', verbose_name='candidature')),
                ('role', models.ForeignKey(to='election.Role', related_name='vote', verbose_name='role')),
            ],
        ),
        migrations.AddField(
            model_name='candidature',
            name='liste',
            field=models.ForeignKey(to='election.List', related_name='candidature', verbose_name='list'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='role',
            field=models.ForeignKey(to='election.Role', related_name='candidature', verbose_name='role'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, related_name='candidate', verbose_name='user'),
        ),
    ]
