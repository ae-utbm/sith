from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0022_auto_20170822_2232")]

    operations = [
        migrations.AddField(
            model_name="preferences",
            name="notify_on_click",
            field=models.BooleanField(
                verbose_name="get a notification for every click", default=False
            ),
        ),
        migrations.AddField(
            model_name="preferences",
            name="notify_on_refill",
            field=models.BooleanField(
                verbose_name="get a notification for every refilling", default=False
            ),
        ),
        migrations.AlterField(
            model_name="preferences",
            name="show_my_stats",
            field=models.BooleanField(
                verbose_name="show your stats to others", default=False
            ),
        ),
        migrations.AlterField(
            model_name="preferences",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="_preferences",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
