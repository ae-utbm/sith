# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0002_auto_20160718_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='location',
            field=models.CharField(max_length=20, verbose_name='location', choices=[('BELFORT', 'Belfort'), ('SEVENANS', 'Sevenans'), ('MONTBELIARD', 'Montbéliard')], default='BELFORT'),
            preserve_default=False,
        ),
    ]
