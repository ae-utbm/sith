# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('election', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='candidature',
            name='has_voted',
        ),
        migrations.AddField(
            model_name='role',
            name='has_voted',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='has_voted', verbose_name='has voted'),
        ),
    ]
