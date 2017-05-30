# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0003_auto_20170510_1754'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forummessage',
            options={'ordering': ['-date']},
        ),
        migrations.AlterModelOptions(
            name='forumtopic',
            options={'ordering': ['-_last_message__date']},
        ),
        migrations.AddField(
            model_name='forum',
            name='_last_message',
            field=models.ForeignKey(related_name='forums_where_its_last', null=True, to='forum.ForumMessage', verbose_name='the last message'),
        ),
        migrations.AddField(
            model_name='forum',
            name='_topic_number',
            field=models.IntegerField(verbose_name='number of topics', default=0),
        ),
        migrations.AddField(
            model_name='forummessage',
            name='_deleted',
            field=models.BooleanField(verbose_name='is deleted', default=False),
        ),
        migrations.AddField(
            model_name='forumtopic',
            name='_last_message',
            field=models.ForeignKey(related_name='+', null=True, to='forum.ForumMessage', verbose_name='the last message'),
        ),
        migrations.AddField(
            model_name='forumtopic',
            name='_message_number',
            field=models.IntegerField(verbose_name='number of messages', default=0),
        ),
        migrations.AddField(
            model_name='forumtopic',
            name='_title',
            field=models.CharField(max_length=64, verbose_name='title', blank=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='description',
            field=models.CharField(max_length=512, verbose_name='description', default=''),
        ),
        migrations.AlterField(
            model_name='forum',
            name='id',
            field=models.AutoField(serialize=False, db_index=True, primary_key=True),
        ),
    ]
