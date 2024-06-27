from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0014_auto_20161210_0009")]

    operations = [
        migrations.AddField(
            model_name="sithfile",
            name="moderator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="moderated_files",
                verbose_name="owner",
                default=0,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        )
    ]
