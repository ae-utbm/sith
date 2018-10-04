# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0005_auto_20160826_2330")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="buying_groups",
            field=models.ManyToManyField(
                related_name="products",
                verbose_name="buying groups",
                blank=True,
                to="core.Group",
            ),
        )
    ]
