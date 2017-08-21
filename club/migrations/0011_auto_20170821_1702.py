# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0010_auto_20170817_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailing',
            name='is_moderated',
            field=models.BooleanField(default=False, verbose_name='is moderated'),
        ),
        migrations.AddField(
            model_name='mailing',
            name='moderator',
            field=models.ForeignKey(related_name='moderated_mailings', to=settings.AUTH_USER_MODEL, null=True, verbose_name='moderator'),
        ),
    ]
