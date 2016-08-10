# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='home',
            field=models.OneToOneField(null=True, verbose_name='home', to='core.SithFile', blank=True, related_name='home_of'),
        ),
    ]
