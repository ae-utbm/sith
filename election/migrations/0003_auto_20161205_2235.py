# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0002_candidate_program'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='responsability',
            field=models.ForeignKey(verbose_name='responsability', to='election.Responsability', related_name='candidate'),
        ),
        migrations.AlterField(
            model_name='responsability',
            name='election',
            field=models.ForeignKey(verbose_name='election', to='election.Election', related_name='responsability'),
        ),
    ]
