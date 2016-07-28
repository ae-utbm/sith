# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0002_auto_20160718_1805'),
        ('launderette', '0002_auto_20160728_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='launderette',
            name='sellers',
            field=models.ManyToManyField(to='subscription.Subscriber', verbose_name='sellers', related_name='launderettes'),
        ),
    ]
