# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0005_forumuserinfo_read_messages'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forumuserinfo',
            name='read_messages',
        ),
        migrations.AddField(
            model_name='forummessage',
            name='readers',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='read_messages', verbose_name='readers'),
        ),
    ]
