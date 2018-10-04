# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0004_auto_20160826_1907")]

    operations = [
        migrations.AlterField(
            model_name="counter",
            name="club",
            field=models.ForeignKey(
                verbose_name="club", to="club.Club", related_name="counters"
            ),
        ),
        migrations.AlterField(
            model_name="counter",
            name="products",
            field=models.ManyToManyField(
                blank=True,
                related_name="counters",
                to="counter.Product",
                verbose_name="products",
            ),
        ),
        migrations.AlterField(
            model_name="permanency",
            name="activity",
            field=models.DateTimeField(
                auto_now=True, verbose_name="last activity date"
            ),
        ),
    ]
