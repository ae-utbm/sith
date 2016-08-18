# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eboutic', '0003_auto_20160818_1738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='payment_method',
        ),
    ]
