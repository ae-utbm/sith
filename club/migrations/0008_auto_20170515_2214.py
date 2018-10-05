# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("club", "0007_auto_20170324_0917")]

    operations = [
        migrations.AlterField(
            model_name="club",
            name="id",
            field=models.AutoField(primary_key=True, serialize=False, db_index=True),
        )
    ]
