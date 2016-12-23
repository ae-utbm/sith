# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('com', '0002_news_newsdate'),
    ]

    operations = [
        migrations.RenameField(
            model_name='news',
            old_name='owner',
            new_name='author',
        ),
        migrations.AlterField(
            model_name='news',
            name='moderator',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='moderated_news', verbose_name='moderator'),
        ),
    ]
