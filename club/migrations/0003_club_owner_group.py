# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('club', '0002_auto_20160202_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='owner_group',
            field=models.ForeignKey(default=1, to='core.Group', related_name='owned_club'),
        ),
    ]
