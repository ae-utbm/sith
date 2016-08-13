# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0002_club_home'),
    ]

    operations = [
        migrations.AlterField(
            model_name='club',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
    ]
