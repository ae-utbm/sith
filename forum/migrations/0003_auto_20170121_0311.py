# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_forumtopic_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forumtopic',
            options={'ordering': ['messages__date', '-id']},
        ),
        migrations.AddField(
            model_name='forummessage',
            name='date',
            field=models.DateTimeField(verbose_name='date', default=django.utils.timezone.now),
        ),
    ]
