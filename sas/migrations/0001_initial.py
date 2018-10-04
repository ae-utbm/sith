# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0006_auto_20161108_1703")]

    operations = [
        migrations.CreateModel(
            name="Album", fields=[], options={"proxy": True}, bases=("core.sithfile",)
        ),
        migrations.CreateModel(
            name="Picture", fields=[], options={"proxy": True}, bases=("core.sithfile",)
        ),
    ]
