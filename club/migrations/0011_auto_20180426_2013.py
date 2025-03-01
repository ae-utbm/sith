from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("club", "0010_auto_20170912_2028")]

    operations = [
        migrations.AlterField(
            model_name="club",
            name="owner_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=lambda: settings.SITH_ROOT_USER_ID,
                related_name="owned_club",
                to="core.Group",
            ),
        )
    ]
