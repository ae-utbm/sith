# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_home'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar_pict',
            field=models.OneToOneField(related_name='avatar_of', verbose_name='avatar', to='core.SithFile', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_pict',
            field=models.OneToOneField(related_name='profile_of', verbose_name='profile', to='core.SithFile', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='scrub_pict',
            field=models.OneToOneField(related_name='scrub_of', verbose_name='scrub', to='core.SithFile', null=True, blank=True),
        ),
    ]
