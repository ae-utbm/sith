# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0013_customer_recorded_products")]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="recorded_products",
            field=models.IntegerField(verbose_name="recorded product", default=0),
        )
    ]
