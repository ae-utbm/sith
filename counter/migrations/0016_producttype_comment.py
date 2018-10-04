# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("counter", "0015_merge")]

    operations = [
        migrations.AddField(
            model_name="producttype",
            name="comment",
            field=models.TextField(verbose_name="comment", blank=True, null=True),
        )
    ]
