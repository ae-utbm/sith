# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.IntegerField(verbose_name='role', default=0, choices=[(0, 'Curious'), (1, 'Active member'), (2, 'Board member'), (3, 'IT supervisor'), (4, 'Secretary'), (5, 'Communication supervisor'), (7, 'Treasurer'), (9, 'Vice-President'), (10, 'President')]),
        ),
    ]
