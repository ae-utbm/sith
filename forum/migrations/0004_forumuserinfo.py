# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0003_forum_owner_club'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumUserInfo',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('last_read_date', models.DateTimeField(verbose_name='last read date', default=datetime.datetime(1999, 1, 1, 0, 0, tzinfo=utc))),
                ('user', models.OneToOneField(related_name='_forum_infos', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
