# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0006_auto_20170128_2243'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumMessageMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date')),
                ('action', models.CharField(max_length=16, choices=[('EDIT', 'Edit'), ('DELETE', 'Delete'), ('UNDELETE', 'Undelete')], verbose_name='action')),
                ('message', models.ForeignKey(related_name='metas', to='forum.ForumMessage')),
                ('user', models.ForeignKey(related_name='forum_message_metas', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
