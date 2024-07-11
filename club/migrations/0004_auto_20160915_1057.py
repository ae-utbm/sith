from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("club", "0003_auto_20160902_2042")]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                verbose_name="user",
                related_name="memberships",
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
