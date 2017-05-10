# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trombi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trombiuser',
            name='profile_pict',
            field=models.ImageField(null=True, blank=True, help_text='The profile picture you want in the trombi (warning: this picture may be published)', verbose_name='profile pict', upload_to='trombi'),
        ),
        migrations.AddField(
            model_name='trombiuser',
            name='scrub_pict',
            field=models.ImageField(null=True, blank=True, help_text='The scrub picture you want in the trombi (warning: this picture may be published)', verbose_name='scrub pict', upload_to='trombi'),
        ),
    ]
