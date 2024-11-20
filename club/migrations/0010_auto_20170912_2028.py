from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0024_auto_20170906_1317"), ("club", "0010_club_logo")]

    operations = [
        migrations.AddField(
            model_name="club",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="is active"),
        ),
        migrations.AddField(
            model_name="club",
            name="page",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="club",
                blank=True,
                null=True,
                to="core.Page",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="short_description",
            field=models.CharField(
                verbose_name="short description",
                max_length=1000,
                default="",
                blank=True,
                null=True,
            ),
        ),
    ]
