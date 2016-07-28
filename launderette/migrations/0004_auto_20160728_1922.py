# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0003_launderette_sellers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='launderette',
            name='sellers',
            field=models.ManyToManyField(blank=True, to='subscription.Subscriber', verbose_name='sellers', related_name='launderettes'),
        ),
    ]
