# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20151123_0948'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='name',
            field=models.CharField(verbose_name='page name', default='guy', max_length=30),
            preserve_default=False,
        ),
    ]
