# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("election", "0002_election_archived")]

    operations = [
        migrations.AlterModelOptions(name="role", options={"ordering": ("order",)}),
        migrations.AddField(
            model_name="role",
            name="order",
            field=models.PositiveIntegerField(editable=False, default=0, db_index=True),
            preserve_default=False,
        ),
    ]
