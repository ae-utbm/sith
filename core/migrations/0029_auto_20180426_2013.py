from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import core.models


class Migration(migrations.Migration):
    dependencies = [("core", "0028_auto_20171216_2044")]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="owner_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                verbose_name="owner group",
                default=core.models.Page.get_default_owner_group,
                related_name="owned_page",
                to="core.Group",
            ),
        )
    ]
