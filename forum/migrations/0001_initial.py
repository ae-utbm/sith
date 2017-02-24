# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0019_preferences_receive_weekmail'),
    ]

    operations = [
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('description', models.CharField(default='', verbose_name='description', max_length=256)),
                ('is_category', models.BooleanField(default=False, verbose_name='is a category')),
                ('edit_groups', models.ManyToManyField(default=[4], related_name='editable_forums', blank=True, to='core.Group')),
                ('owner_group', models.ForeignKey(default=12, related_name='owned_forums', to='core.Group')),
                ('parent', models.ForeignKey(null=True, related_name='children', blank=True, to='forum.Forum')),
                ('view_groups', models.ManyToManyField(default=[2], related_name='viewable_forums', blank=True, to='core.Group')),
            ],
        ),
        migrations.CreateModel(
            name='ForumMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(default='', verbose_name='title', blank=True, max_length=64)),
                ('message', models.TextField(default='', verbose_name='message')),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date')),
                ('author', models.ForeignKey(related_name='forum_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ForumTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(default='', verbose_name='title', max_length=64)),
                ('description', models.CharField(default='', verbose_name='description', max_length=256)),
                ('author', models.ForeignKey(related_name='forum_topics', to=settings.AUTH_USER_MODEL)),
                ('forum', models.ForeignKey(related_name='topics', to='forum.Forum')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.AddField(
            model_name='forummessage',
            name='topic',
            field=models.ForeignKey(related_name='messages', to='forum.ForumTopic'),
        ),
    ]
