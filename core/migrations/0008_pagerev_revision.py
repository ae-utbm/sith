# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_user_is_superuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagerev',
            name='revision',
            field=models.IntegerField(default=1, verbose_name='revision'),
            preserve_default=False,
        ),
    ]
