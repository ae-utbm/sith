# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0001_initial'),
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubaccount',
            name='club',
            field=models.OneToOneField(to='club.Club', related_name='club_account'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='club',
            field=models.ForeignKey(to='club.Club', related_name='bank_accounts'),
        ),
    ]
