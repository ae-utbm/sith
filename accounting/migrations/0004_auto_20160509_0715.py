# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_auto_20160509_0712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='club',
            field=models.ForeignKey(related_name='products', to='club.Club'),
        ),
    ]
