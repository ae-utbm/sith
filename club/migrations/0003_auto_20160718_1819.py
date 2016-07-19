# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0002_auto_20160718_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='club',
            field=models.ForeignKey(to='club.Club', verbose_name='club', related_name='members'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='user', related_name='membership'),
        ),
    ]
