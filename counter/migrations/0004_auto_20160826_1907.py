# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0003_permanency_activity")]

    operations = [
        migrations.AlterField(
            model_name="permanency",
            name="end",
            field=models.DateTimeField(verbose_name="end date", null=True),
        )
    ]
