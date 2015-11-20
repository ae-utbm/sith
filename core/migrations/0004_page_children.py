# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20151119_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='children',
            field=models.ForeignKey(to='core.Page', related_name='parent', null=True),
        ),
    ]
