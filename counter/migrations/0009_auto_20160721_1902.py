# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0008_auto_20160718_1805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='counter',
            name='type',
            field=models.CharField(max_length=255, verbose_name='subscription type', choices=[('BAR', 'Bar'), ('OFFICE', 'Office'), ('EBOUTIC', 'Eboutic')]),
        ),
    ]
