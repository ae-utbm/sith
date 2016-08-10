# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_home'),
        ('club', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='home',
            field=models.OneToOneField(blank=True, null=True, related_name='home_of_club', verbose_name='home', to='core.SithFile'),
        ),
    ]
