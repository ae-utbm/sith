# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20161209_2338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(verbose_name='type', max_length=32, default='GENERIC', choices=[('FILE_MODERATION', 'New files to be moderated'), ('SAS_MODERATION', 'New pictures/album to be moderated in the SAS'), ('NEW_PICTURES', "You've been identified on some pictures"), ('REFILLING', 'You just refilled of %s €'), ('SELLING', 'You just bought %s'), ('GENERIC', 'You have a notification')]),
        ),
    ]
