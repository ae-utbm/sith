# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0006_auto_20161229_0040'),
        ('forum', '0002_auto_20170128_1958'),
    ]

    operations = [
        migrations.AddField(
            model_name='forum',
            name='owner_club',
            field=models.ForeignKey(related_name='owned_forums', verbose_name='owner club', to='club.Club', default=1),
        ),
    ]
