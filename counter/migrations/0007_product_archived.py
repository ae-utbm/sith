# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0006_auto_20160831_1304")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="archived",
            field=models.BooleanField(verbose_name="archived", default=False),
        )
    ]
