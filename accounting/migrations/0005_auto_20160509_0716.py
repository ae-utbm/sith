# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0004_auto_20160509_0715'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='club',
            field=models.ForeignKey(related_name='bank_accounts', to='club.Club'),
        ),
    ]
