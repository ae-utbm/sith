# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_page_full_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'permissions': ()},
        ),
    ]
