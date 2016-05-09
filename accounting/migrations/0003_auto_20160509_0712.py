# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0001_initial'),
        ('accounting', '0002_auto_20160502_0952'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='club',
            field=models.OneToOneField(to='club.Club', related_name='bank_accounts', default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='club',
            field=models.OneToOneField(to='club.Club', related_name='products', default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='clubaccount',
            name='club',
            field=models.OneToOneField(related_name='club_account', to='club.Club'),
        ),
    ]
