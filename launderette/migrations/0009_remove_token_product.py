# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0008_token_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='token',
            name='product',
        ),
    ]
