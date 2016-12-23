# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('election', '0005_auto_20161223_2240'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='has_voted',
        ),
        migrations.AddField(
            model_name='election',
            name='voters',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='has voted', related_name='has_voted'),
        ),
    ]
