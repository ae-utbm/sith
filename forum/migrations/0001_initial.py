# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('description', models.CharField(default='', verbose_name='description', max_length=256)),
                ('is_category', models.BooleanField(default=False, verbose_name='is a category')),
                ('edit_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='editable_forums')),
                ('owner_group', models.ForeignKey(to='core.Group', default=4, related_name='owned_forums')),
                ('parent', models.ForeignKey(blank=True, null=True, to='forum.Forum', related_name='children')),
                ('view_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='viewable_forums')),
            ],
        ),
        migrations.CreateModel(
            name='ForumMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(default='', blank=True, verbose_name='title', max_length=64)),
                ('message', models.TextField(verbose_name='message', default='')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='forum_messages')),
            ],
        ),
        migrations.CreateModel(
            name='ForumTopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='forum_topics')),
                ('forum', models.ForeignKey(to='forum.Forum', related_name='topics')),
            ],
        ),
        migrations.AddField(
            model_name='forummessage',
            name='topic',
            field=models.ForeignKey(to='forum.ForumTopic', related_name='messages'),
        ),
    ]
