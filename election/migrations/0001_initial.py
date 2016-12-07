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
            name='Candidate',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('program', models.TextField(blank=True, null=True, verbose_name='description')),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('start_proposal', models.DateTimeField(verbose_name='start proposal')),
                ('end_proposal', models.DateTimeField(verbose_name='end proposal')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(verbose_name='end date')),
            ],
        ),
        migrations.CreateModel(
            name='Responsability',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('election', models.ForeignKey(to='election.Election', verbose_name='election', related_name='responsability')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('candidate', models.ManyToManyField(to='election.Candidate', related_name='vote', verbose_name='candidate')),
                ('election', models.ForeignKey(to='election.Election', verbose_name='election', related_name='vote')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='user', related_name='vote')),
            ],
        ),
        migrations.AddField(
            model_name='candidate',
            name='responsability',
            field=models.ForeignKey(to='election.Responsability', verbose_name='responsability', related_name='candidate'),
        ),
        migrations.AddField(
            model_name='candidate',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='user', related_name='candidate'),
        ),
    ]
