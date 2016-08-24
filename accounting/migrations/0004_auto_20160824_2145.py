# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_auto_20160824_1732'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accountingtype',
            options={'ordering': ['movement_type', 'code'], 'verbose_name': 'accounting type'},
        ),
        migrations.AlterModelOptions(
            name='bankaccount',
            options={'ordering': ['club', 'name'], 'verbose_name': 'Bank account'},
        ),
        migrations.AlterModelOptions(
            name='clubaccount',
            options={'ordering': ['bank_account', 'name'], 'verbose_name': 'Club account'},
        ),
        migrations.AlterModelOptions(
            name='generaljournal',
            options={'ordering': ['-start_date'], 'verbose_name': 'General journal'},
        ),
        migrations.AlterModelOptions(
            name='simplifiedaccountingtype',
            options={'ordering': ['accounting_type__movement_type', 'accounting_type__code'], 'verbose_name': 'simplified type'},
        ),
    ]
