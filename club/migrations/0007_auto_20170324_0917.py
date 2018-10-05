# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("club", "0006_auto_20161229_0040")]

    operations = [
        migrations.AlterModelOptions(
            name="club", options={"ordering": ["name", "unix_name"]}
        )
    ]
