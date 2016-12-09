# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_notification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='text',
        ),
        migrations.AddField(
            model_name='notification',
            name='param',
            field=models.CharField(verbose_name='param', default='', max_length=128),
        ),
        migrations.AddField(
            model_name='notification',
            name='viewed',
            field=models.BooleanField(verbose_name='viewed', default=False),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(verbose_name='type', default='GENERIC', choices=[('FILE_MODERATION', 'New files to be moderated'), ('SAS_MODERATION', 'New pictures/album to be moderated in the SAS'), ('NEW_PICTURES', "You've been identified on some pictures"), ('REFILLING', 'You just refilled of %(amount)s €'), ('SELLING', 'You just bought %(selling)s'), ('GENERIC', 'You have a notification')], max_length=32),
        ),
    ]
