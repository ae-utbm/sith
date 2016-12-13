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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('program', models.TextField(blank=True, null=True, verbose_name='description')),
                ('has_voted', models.ManyToManyField(related_name='has_voted', to=settings.AUTH_USER_MODEL, verbose_name='has_voted')),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('start_candidature', models.DateTimeField(verbose_name='start candidature')),
                ('end_candidature', models.DateTimeField(verbose_name='end candidature')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(verbose_name='end date')),
            ],
        ),
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('election', models.ForeignKey(related_name='role', to='election.Election', verbose_name='election')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('candidature', models.ManyToManyField(related_name='vote', to='election.Candidature', verbose_name='candidature')),
                ('role', models.ForeignKey(related_name='vote', to='election.Role', verbose_name='role')),
            ],
        ),
        migrations.AddField(
            model_name='candidature',
            name='role',
            field=models.ForeignKey(related_name='candidature', to='election.Role', verbose_name='role'),
        ),
        migrations.AddField(
            model_name='candidature',
            name='user',
            field=models.ForeignKey(blank=True, related_name='candidate', to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]
