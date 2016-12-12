# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_sithfile_moderator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sithfile',
            name='moderator',
            field=models.ForeignKey(related_name='moderated_files', blank=True, null=True, to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
    ]
