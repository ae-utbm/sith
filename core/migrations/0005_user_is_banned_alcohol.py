# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_user_godfathers'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_banned_alcohol',
            field=models.BooleanField(help_text='Designates whether this user is denyed from buying alchool. ', verbose_name='banned from buying alcohol', default=False),
        ),
    ]
