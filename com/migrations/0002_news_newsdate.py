# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0005_auto_20161120_1149'),
        ('com', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(max_length=64, verbose_name='title')),
                ('summary', models.TextField(verbose_name='summary')),
                ('content', models.TextField(verbose_name='content')),
                ('type', models.CharField(max_length=16, choices=[('NOTICE', 'Notice'), ('EVENT', 'Event'), ('WEEKLY', 'Weekly'), ('CALL', 'Call')], default='EVENT', verbose_name='type')),
                ('is_moderated', models.BooleanField(default=False, verbose_name='is moderated')),
                ('club', models.ForeignKey(to='club.Club', verbose_name='club', related_name='news')),
                ('moderator', models.ForeignKey(verbose_name='owner', to=settings.AUTH_USER_MODEL, related_name='moderated_news', null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='owner', related_name='owned_news')),
            ],
        ),
        migrations.CreateModel(
            name='NewsDate',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('start_date', models.DateTimeField(null=True, blank=True, verbose_name='start_date')),
                ('end_date', models.DateTimeField(null=True, blank=True, verbose_name='end_date')),
                ('news', models.ForeignKey(to='com.News', verbose_name='news_date', related_name='dates')),
            ],
        ),
    ]
