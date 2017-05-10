# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matmat', '0002_auto_20170510_1754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='matmatcomment',
            name='is_moderated',
        ),
    ]
