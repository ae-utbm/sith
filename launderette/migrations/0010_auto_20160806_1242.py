# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0009_remove_token_product'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='token',
            options={'verbose_name': 'Token', 'ordering': ['name']},
        ),
    ]
