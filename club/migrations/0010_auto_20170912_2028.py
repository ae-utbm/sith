# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from club.models import Club


def generate_club_pages(apps, schema_editor):
    for club in Club.objects.all():
        club.make_page()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20170906_1317'),
        ('club', '0009_auto_20170822_2232'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='is active'),
        ),
        migrations.AddField(
            model_name='club',
            name='page',
            field=models.OneToOneField(related_name='club', blank=True, null=True, to='core.Page'),
        ),
        migrations.RunPython(generate_club_pages),
    ]
