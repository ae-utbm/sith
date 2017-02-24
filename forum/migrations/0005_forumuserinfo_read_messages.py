# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0004_forumuserinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumuserinfo',
            name='read_messages',
            field=models.ManyToManyField(to='forum.ForumMessage', related_name='readers', verbose_name='read messages'),
        ),
    ]
