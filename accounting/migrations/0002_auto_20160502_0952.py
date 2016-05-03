# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='journal',
            field=models.ForeignKey(to='accounting.GeneralJournal', related_name='operations'),
        ),
    ]
